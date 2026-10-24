#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rigorous comparison of Median/MAD and EWMA anomaly detectors.

This module evaluates the two existing detectors without rewriting or tuning
either. Ground truth is derived directly from the generator's documented
construction in scripts/generate_hospital_data.py.

Important distinctions
----------------------
- The regional outbreak is a SUSTAINED increase over the last 14 days for
  HOSP_TUN and HOSP_SOU. Labeling the ENTIRE 90-day dataset as anomalous would
  be incorrect; only those specific days/hospitals are the synthetic event days.
- The reporting error is a SINGLE extreme one-day spike at HOSP_TUN only.
  We treat it as a simulated data-quality event, NOT a confirmed disease outbreak.
- Only days with valid historical context (as defined by each detector) are
  evaluated in the confusion matrix. Days before the detector can issue alerts
  are excluded to avoid penalizing the detectors for their warm-up requirements.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any

from ai_service.anomaly_detector import AnomalyDetector
from ai_service.ewma_detector import EWMADetector


class DetectorBenchmark:
    """Compare Median/MAD and EWMA detectors against generator-derived ground truth."""

    # Generator constants (must match scripts/generate_hospital_data.py)
    SEED = 12345
    START_DATE = date(2024, 1, 1)
    DAYS = 90
    HOSPITALS = ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"]
    OUTBREAK_START_OFFSET = DAYS - 14  # final 14 days

    def __init__(self, data_dir: Path = None, reports_dir: Path = None):
        project_root = Path(__file__).parent.parent
        self.data_dir = data_dir or (project_root / "data" / "synthetic")
        self.reports_dir = reports_dir or (project_root / "reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_dates() -> List[str]:
        """Generate the date sequence used by the generator."""
        dates = []
        cur = DetectorBenchmark.START_DATE
        for _ in range(DetectorBenchmark.DAYS):
            dates.append(cur.isoformat())
            cur += timedelta(days=1)
        return dates

    @staticmethod
    def _compute_reporting_error_spike_offset() -> int:
        """Compute spike_day_offset by replaying RNG consumption order from generator."""
        import random
        from datetime import date
        rng = random.Random(DetectorBenchmark.SEED)
        days = DetectorBenchmark.DAYS
        start_date = DetectorBenchmark.START_DATE
        HOSPITALS = [
            {"hospital_id": "HOSP_TUN", "city": "Tunis"},
            {"hospital_id": "HOSP_SOU", "city": "Sousse"},
            {"hospital_id": "HOSP_SFX", "city": "Sfax"},
        ]
        # generate_normal
        for h in HOSPITALS:
            baseline = rng.randint(12, 16)
            for i in range(days):
                fluct = rng.randint(-3, 3)
        # generate_regional_outbreak
        outbreak_start_offset = days - 14
        for h in HOSPITALS:
            baseline = rng.randint(12, 16)
            for i in range(days):
                if i >= outbreak_start_offset and h["hospital_id"] in ("HOSP_TUN", "HOSP_SOU"):
                    spike = rng.randint(15, 25)
                else:
                    fluct = rng.randint(-2, 2)
        # generate_reporting_error
        spike_hospital = "HOSP_TUN"
        spike_day_offset = rng.randint(10, days - 20)
        for h in HOSPITALS:
            baseline = rng.randint(12, 16)
            for i in range(days):
                if h["hospital_id"] == spike_hospital and i == spike_day_offset:
                    cases = baseline + rng.randint(80, 120)
                else:
                    fluct = rng.randint(-2, 2)
        return spike_day_offset

    def build_ground_truth(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Build ground truth labels directly from generator construction.
        Returns: {scenario: {hospital_id: {date: label}}}
        label = 1 if this day/hospital is a synthetic positive event, else 0.
        """
        dates = self._get_dates()
        gt: Dict[str, Dict[str, Dict[str, int]]] = {}

        # Normal: no synthetic events
        gt["normal"] = {h: {d: 0 for d in dates} for h in self.HOSPITALS}

        # Regional outbreak: last 14 days for TUN and SOU only
        gt["regional_outbreak"] = {h: {d: 0 for d in dates} for h in self.HOSPITALS}
        outbreak_dates = set(dates[self.OUTBREAK_START_OFFSET:])
        for h in ["HOSP_TUN", "HOSP_SOU"]:
            for d in outbreak_dates:
                gt["regional_outbreak"][h][d] = 1

        # Reporting error: single extreme spike on HOSP_TUN - replay generator RNG order
        spike_day_offset = self._compute_reporting_error_spike_offset()
        gt["reporting_error"] = {h: {d: 0 for d in dates} for h in self.HOSPITALS}
        gt["reporting_error"]["HOSP_TUN"][dates[spike_day_offset]] = 1

        return gt

    def _evaluate_detector(self, detector_name: str, detector, gt: Dict) -> Dict[str, Any]:
        """Evaluate a single detector across all scenarios."""
        results = {}

        for scenario in ["normal", "regional_outbreak", "reporting_error"]:
            csv_path = self.data_dir / f"{scenario}.csv"
            det_results = detector.analyze_file(csv_path)

            scenario_metrics = {
                "hospitals": {},
                "overall": {"TP": 0, "FP": 0, "TN": 0, "FN": 0},
                "events": {}
            }

            # For event detection
            if scenario == "regional_outbreak":
                # Event exists on TUN and SOU for last 14 days
                event_hospitals = ["HOSP_TUN", "HOSP_SOU"]
                onset_date = self._get_dates()[self.OUTBREAK_START_OFFSET]
                scenario_metrics["events"] = {
                    "type": "sustained_regional_increase",
                    "onset_date": onset_date,
                    "event_hospitals": event_hospitals,
                    "notes": "Sustained increase over last 14 days (days >= outbreak_start_offset)"
                }
            elif scenario == "reporting_error":
                spike_day_offset = self._compute_reporting_error_spike_offset()
                spike_date = self._get_dates()[spike_day_offset]
                scenario_metrics["events"] = {
                    "type": "single_day_extreme_spike",
                    "spike_date": spike_date,
                    "event_hospital": "HOSP_TUN",
                    "notes": "Simulated data-quality event, NOT a confirmed disease outbreak"
                }
            else:
                scenario_metrics["events"] = {"type": "none"}

            for hid in self.HOSPITALS:
                hosp_results = det_results.get(hid, [])
                tp = fp = tn = fn = 0

                # Build lookup of detector predictions by date
                pred_by_date = {r["date"]: bool(r["anomaly_flag"]) for r in hosp_results}

                # Only evaluate days with valid historical context
                for d, true_label in gt[scenario][hid].items():
                    if d not in pred_by_date:
                        continue  # no prediction (warm-up period or not analyzed)
                    pred_label = pred_by_date[d]
                    if pred_label and true_label == 1:
                        tp += 1
                    elif pred_label and true_label == 0:
                        fp += 1
                    elif not pred_label and true_label == 0:
                        tn += 1
                    elif not pred_label and true_label == 1:
                        fn += 1

                precision, recall, f1 = self._compute_metrics(tp, fp, tn, fn)
                scenario_metrics["hospitals"][hid] = {
                    "TP": tp, "FP": fp, "TN": tn, "FN": fn,
                    "precision": precision, "recall": recall, "f1": f1,
                    "evaluated_days": tp + fp + tn + fn
                }
                scenario_metrics["overall"]["TP"] += tp
                scenario_metrics["overall"]["FP"] += fp
                scenario_metrics["overall"]["TN"] += tn
                scenario_metrics["overall"]["FN"] += fn

            o = scenario_metrics["overall"]
            precision, recall, f1 = self._compute_metrics(o["TP"], o["FP"], o["TN"], o["FN"])
            scenario_metrics["overall"]["precision"] = precision
            scenario_metrics["overall"]["recall"] = recall
            scenario_metrics["overall"]["f1"] = f1
            scenario_metrics["overall"]["evaluated_days"] = o["TP"] + o["FP"] + o["TN"] + o["FN"]

            # First detection delay
            if scenario == "regional_outbreak":
                delay = self._first_detection_delay(det_results, gt[scenario], onset_date=self._get_dates()[self.OUTBREAK_START_OFFSET])
                scenario_metrics["first_detection_delay"] = delay
            elif scenario == "reporting_error":
                spike_day_offset = self._compute_reporting_error_spike_offset()
                spike_date = self._get_dates()[spike_day_offset]
                delay = self._first_detection_delay_single(det_results, spike_date, "HOSP_TUN")
                scenario_metrics["first_detection_delay"] = delay

            results[scenario] = scenario_metrics

        return results

    @staticmethod
    def _compute_metrics(tp, fp, tn, fn):
        """Compute precision, recall, F1 with zero-denominator handling."""
        if tp + fp == 0:
            precision = None  # undefined - no positive predictions
        else:
            precision = tp / (tp + fp)

        if tp + fn == 0:
            recall = None  # undefined - no positives to find
        else:
            recall = tp / (tp + fn)

        if precision is None or recall is None or (precision + recall) == 0:
            f1 = None
        else:
            f1 = 2 * precision * recall / (precision + recall)

        return precision, recall, f1

    def _first_detection_delay(self, det_results, gt_scenario, onset_date):
        """First detection delay relative to onset for regional outbreak."""
        delays = []
        for hid in ["HOSP_TUN", "HOSP_SOU"]:
            hosp_results = det_results.get(hid, [])
            # Find first true positive on or after onset
            onset_idx = self._get_dates().index(onset_date)
            for r in hosp_results:
                r_idx = self._get_dates().index(r["date"])
                if r_idx < onset_idx:
                    continue
                if r.get("anomaly_flag") and gt_scenario[hid].get(r["date"], 0) == 1:
                    delays.append(r_idx - onset_idx)
                    break
        if not delays:
            return {"detected": False, "delay_days": None, "details": "No true positive detected on event days"}
        return {"detected": True, "delay_days": min(delays), "max_delay_days": max(delays), "details": f"First TP at {min(delays)} days after onset"}

    def _first_detection_delay_single(self, det_results, spike_date, hid):
        """First detection delay for single spike."""
        hosp_results = det_results.get(hid, [])
        spike_idx = self._get_dates().index(spike_date)
        for r in hosp_results:
            r_idx = self._get_dates().index(r["date"])
            if r["date"] == spike_date and r.get("anomaly_flag"):
                return {"detected": True, "delay_days": 0, "details": "Detected on spike day"}
        # Check if detected at all
        for r in hosp_results:
            if r.get("anomaly_flag"):
                r_idx = self._get_dates().index(r["date"])
                return {"detected": True, "delay_days": r_idx - spike_idx, "details": "Detected off spike day"}
        return {"detected": False, "delay_days": None, "details": "Spike not detected"}

    def threshold_sensitivity(self) -> Dict[str, Any]:
        """Simple threshold sensitivity without changing existing detector defaults."""
        sensitivity = {}

        # For Median/MAD - we can't easily change threshold without recreating detector
        # But we can analyze with different conceptual thresholds by re-running? 
        # The detectors have fixed defaults in practice; let's test with different instances
        for thresh in [2.5, 3.0, 3.5, 4.0]:
            mad_det = AnomalyDetector(window_size=21, threshold=thresh)
            results = mad_det.analyze_file(self.data_dir / "regional_outbreak.csv")
            # Count flags
            total = sum(len([r for r in res if r.get('anomaly_flag')]) for res in results.values())
            sensitivity[f"mad_threshold_{thresh}"] = {"total_flags_regional_outbreak": total}

        for thresh in [2.0, 2.5, 3.0, 3.5]:
            ewma_det = EWMADetector(alpha=0.2, initial_window=21, threshold=thresh)
            results = ewma_det.analyze_file(self.data_dir / "regional_outbreak.csv")
            total = sum(len([r for r in res if r.get('anomaly_flag')]) for res in results.values())
            sensitivity[f"ewma_threshold_{thresh}"] = {"total_flags_regional_outbreak": total}

        return sensitivity

    def run_benchmark(self) -> Dict[str, Any]:
        """Run full benchmark and save report."""
        gt = self.build_ground_truth()

        mad_det = AnomalyDetector(window_size=21, threshold=3.5)
        ewma_det = EWMADetector(alpha=0.2, initial_window=21, threshold=3.0)

        report = {
            "title": "MONITUS Detector Benchmark - Median/MAD vs EWMA",
            "configuration": {
                "mad_detector": {"window_size": 21, "threshold": 3.5, "method": "median_mad"},
                "ewma_detector": {"alpha": 0.2, "initial_window": 21, "threshold": 3.0, "method": "ewma"},
                "data_source": "scripts/generate_hospital_data.py (seed 12345)",
                "hospitals": self.HOSPITALS,
                "days": self.DAYS,
                "start_date": self.START_DATE.isoformat()
            },
            "evaluated_date_range": {
                "note": "Only days with valid historical context per detector are evaluated",
                "mad_warmup": "21 days history required (evaluates from day 22 onward)",
                "ewma_warmup": "21 days seed required (evaluates from day 22 onward)"
            },
            "ground_truth_assumptions": {
                "normal": "No synthetic events labeled as positive",
                "regional_outbreak": f"Sustained increase for HOSP_TUN, HOSP_SOU on days >= {self.OUTBREAK_START_OFFSET} (last 14 days). Sfax not labeled positive. Entire dataset NOT labeled anomalous.",
                "reporting_error": "Single extreme spike on HOSP_TUN only (computed from generator RNG with seed 12345, replaying full generation order). Treated as simulated data-quality event, NOT confirmed disease outbreak.",
                "uncertainty": "Labels derived from documented generator logic by replaying RNG consumption order; exact spike_day_offset computed deterministically from seed."
            },
            "detectors": {}
        }

        for name, det in [("median_mad", mad_det), ("ewma", ewma_det)]:
            report["detectors"][name] = self._evaluate_detector(name, det, gt)

        report["threshold_sensitivity"] = self.threshold_sensitivity()
        report["limitations"] = [
            "Synthetic data only - no clinical accuracy claims",
            "Ground truth based on generator construction, not real outbreaks",
            "Warm-up days excluded from evaluation",
            "Detectors not tuned; default/standard parameters used",
            "Event detection metrics are scenario-specific",
            "Regional outbreak is sustained increase (14 days) - 'first detection' measured from onset",
            "Reporting error treated as data-quality event, not disease outbreak"
        ]

        report_path = self.reports_dir / "detector_benchmark.json"
        with report_path.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        report["report_path"] = str(report_path)

        return report

    def print_comparison_table(self, report: Dict):
        """Print readable CLI comparison table."""
        print("\n" + "=" * 100)
        print("MONITUS DETECTOR BENCHMARK: Median/MAD vs EWMA")
        print("=" * 100)

        print("\nCONFIGURATION:")
        print(f"  Data: {report['configuration']['data_source']}")
        print(f"  Hospitals: {report['configuration']['hospitals']}")
        print(f"  MAD: window={report['configuration']['mad_detector']['window_size']}, threshold={report['configuration']['mad_detector']['threshold']}")
        print(f"  EWMA: alpha={report['configuration']['ewma_detector']['alpha']}, initial_window={report['configuration']['ewma_detector']['initial_window']}, threshold={report['configuration']['ewma_detector']['threshold']}")

        print("\nGROUND TRUTH ASSUMPTIONS:")
        for k, v in report['ground_truth_assumptions'].items():
            if k != 'uncertainty':
                print(f"  {k}: {v}")
        print(f"  uncertainty: {report['ground_truth_assumptions']['uncertainty']}")

        for scenario in ["normal", "regional_outbreak", "reporting_error"]:
            print("\n" + "-" * 100)
            print(f"SCENARIO: {scenario}")
            print("-" * 100)
            events = report['detectors']['median_mad'][scenario]['events']
            print(f"  Event: {events}")

            print(f"\n  {'Detector':<15} {'Hospital':<12} {'TP':>4} {'FP':>4} {'TN':>4} {'FN':>4} {'Prec':>8} {'Recall':>8} {'F1':>8}")
            print(f"  {'-'*15} {'-'*12} {'-'*4} {'-'*4} {'-'*4} {'-'*4} {'-'*8} {'-'*8} {'-'*8}")

            for det_name in ["median_mad", "ewma"]:
                det_data = report['detectors'][det_name][scenario]
                for hid in ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"]:
                    h = det_data['hospitals'][hid]
                    prec = f"{h['precision']:.3f}" if h['precision'] is not None else "N/A"
                    rec = f"{h['recall']:.3f}" if h['recall'] is not None else "N/A"
                    f1 = f"{h['f1']:.3f}" if h['f1'] is not None else "N/A"
                    print(f"  {det_name:<15} {hid:<12} {h['TP']:>4} {h['FP']:>4} {h['TN']:>4} {h['FN']:>4} {prec:>8} {rec:>8} {f1:>8}")
                # overall
                o = det_data['overall']
                prec = f"{o['precision']:.3f}" if o['precision'] is not None else "N/A"
                rec = f"{o['recall']:.3f}" if o['recall'] is not None else "N/A"
                f1 = f"{o['f1']:.3f}" if o['f1'] is not None else "N/A"
                print(f"  {det_name + ' (OVERALL)':<15} {'ALL':<12} {o['TP']:>4} {o['FP']:>4} {o['TN']:>4} {o['FN']:>4} {prec:>8} {rec:>8} {f1:>8}")
                print()

            if 'first_detection_delay' in det_data:
                fd = det_data['first_detection_delay']
                print(f"  First detection delay ({det_name}): {fd}")

        print("\n" + "=" * 100)
        print("THRESHOLD SENSITIVITY (no defaults changed):")
        for k, v in report['threshold_sensitivity'].items():
            print(f"  {k}: {v}")
        print("\nLIMITATIONS:")
        for lim in report['limitations']:
            print(f"  - {lim}")
        print("=" * 100 + "\n")


def main():
    benchmark = DetectorBenchmark()
    report = benchmark.run_benchmark()
    benchmark.print_comparison_table(report)
    print(f"Report saved to: {report['report_path']}")


if __name__ == "__main__":
    main()
