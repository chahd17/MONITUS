#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for detector benchmark.
Uses unittest and standard library only.
"""

import json
import sys
import unittest
from pathlib import Path
import tempfile
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.detector_benchmark import DetectorBenchmark


class TestDetectorBenchmark(unittest.TestCase):
    """Test cases for DetectorBenchmark."""

    def setUp(self):
        self.bench = DetectorBenchmark()
        self.gt = self.bench.build_ground_truth()

    def test_ground_truth_normal_all_zero(self):
        """Normal scenario should have no positive labels."""
        for hid in self.bench.HOSPITALS:
            self.assertTrue(all(v == 0 for v in self.gt["normal"][hid].values()))

    def test_ground_truth_regional_outbreak_correct_hospitals(self):
        """Regional outbreak: only TUN and SOU in last 14 days labeled positive."""
        dates = self.bench._get_dates()
        outbreak_dates = set(dates[self.bench.OUTBREAK_START_OFFSET:])
        for hid in ["HOSP_TUN", "HOSP_SOU"]:
            for d in outbreak_dates:
                self.assertEqual(self.gt["regional_outbreak"][hid][d], 1)
        for hid in ["HOSP_SFX"]:
            for d in outbreak_dates:
                self.assertEqual(self.gt["regional_outbreak"][hid][d], 0)
        # Not all days labeled
        total_pos = sum(sum(v for v in self.gt["regional_outbreak"][h].values()) for h in self.bench.HOSPITALS)
        self.assertEqual(total_pos, 28)  # 2 hospitals * 14 days

    def test_ground_truth_reporting_error_single_spike(self):
        """Reporting error has exactly one positive label on HOSP_TUN."""
        total_pos = sum(sum(v for v in self.gt["reporting_error"][h].values()) for h in self.bench.HOSPITALS)
        self.assertEqual(total_pos, 1)
        # Find it
        for hid in self.bench.HOSPITALS:
            for d, v in self.gt["reporting_error"][hid].items():
                if v == 1:
                    self.assertEqual(hid, "HOSP_TUN")
                    self.assertEqual(d, "2024-02-28")
                    self.assertEqual(self.gt["reporting_error"]["HOSP_TUN"]["2024-02-06"], 0)
                    break

    def test_confusion_counts_structure(self):
        """Confusion counts must be integers."""
        report = self.bench.run_benchmark()
        for det_name in ["median_mad", "ewma"]:
            for scenario in ["normal", "regional_outbreak", "reporting_error"]:
                for hid in self.bench.HOSPITALS:
                    h = report["detectors"][det_name][scenario]["hospitals"][hid]
                    for k in ["TP", "FP", "TN", "FN"]:
                        self.assertIsInstance(h[k], int)

    def test_metric_calculation_zero_denominators(self):
        """Metrics should handle zero denominators gracefully."""
        prec, rec, f1 = self.bench._compute_metrics(0, 0, 10, 0)
        self.assertIsNone(prec)
        self.assertIsNone(rec)
        self.assertIsNone(f1)

        prec, rec, f1 = self.bench._compute_metrics(0, 5, 10, 0)
        self.assertEqual(prec, 0.0)
        self.assertIsNone(rec)
        self.assertIsNone(f1)

        prec, rec, f1 = self.bench._compute_metrics(0, 0, 10, 5)
        self.assertIsNone(prec)
        self.assertEqual(rec, 0.0)
        self.assertIsNone(f1)

    def test_metric_calculation_normal_case(self):
        """Normal metric calculation."""
        prec, rec, f1 = self.bench._compute_metrics(10, 2, 80, 5)
        self.assertAlmostEqual(prec, 10/12)
        self.assertAlmostEqual(rec, 10/15)
        self.assertAlmostEqual(f1, 2*(10/12)*(10/15)/((10/12)+(10/15)))

    def test_first_detection_delay_structure(self):
        """First detection delay has expected structure."""
        report = self.bench.run_benchmark()
        for det_name in ["median_mad", "ewma"]:
            fd = report["detectors"][det_name]["regional_outbreak"]["first_detection_delay"]
            self.assertIn("detected", fd)
            self.assertIn("delay_days", fd)

    def test_evaluated_days_only_with_context(self):
        """Only days with valid historical context are evaluated."""
        report = self.bench.run_benchmark()
        # Each hospital should have 69 evaluated days (90 - 21 warmup)
        for det_name in ["median_mad", "ewma"]:
            for scenario in ["normal", "regional_outbreak"]:
                for hid in self.bench.HOSPITALS:
                    self.assertEqual(report["detectors"][det_name][scenario]["hospitals"][hid]["evaluated_days"], 69)

    def test_report_generation(self):
        """Report is generated with required fields."""
        report = self.bench.run_benchmark()
        required = ["title", "configuration", "evaluated_date_range", "ground_truth_assumptions",
                    "detectors", "threshold_sensitivity", "limitations", "report_path"]
        for r in required:
            self.assertIn(r, report)
        self.assertTrue(Path(report["report_path"]).exists())

    def test_report_json_valid(self):
        """Generated JSON is valid."""
        report_path = project_root / "reports" / "detector_benchmark.json"
        self.bench.run_benchmark()
        with report_path.open() as f:
            data = json.load(f)
        self.assertIn("detectors", data)

    def test_reporting_error_correct_labeling_for_detectors(self):
        """Detection on 2024-02-28 must be evaluated against true positive label."""
        gt = self.bench.build_ground_truth()
        self.assertEqual(gt["reporting_error"]["HOSP_TUN"]["2024-02-28"], 1)
        self.assertEqual(gt["reporting_error"]["HOSP_TUN"]["2024-02-06"], 0)
        from ai_service.anomaly_detector import AnomalyDetector
        from ai_service.ewma_detector import EWMADetector
        from pathlib import Path
        mad = AnomalyDetector(window_size=21, threshold=3.5)
        ewma = EWMADetector(alpha=0.2, initial_window=21, threshold=3.0)
        mad_res = mad.analyze_file(Path('data/synthetic/reporting_error.csv'))
        ewma_res = ewma.analyze_file(Path('data/synthetic/reporting_error.csv'))
        # Find flags
        mad_flags = [r for r in mad_res['HOSP_TUN'] if r['anomaly_flag']]
        ewma_flags = [r for r in ewma_res['HOSP_TUN'] if r['anomaly_flag']]
        self.assertTrue(any(r['date']=='2024-02-28' for r in mad_flags))
        self.assertTrue(any(r['date']=='2024-02-28' for r in ewma_flags))

    def test_ground_truth_not_from_predictions(self):
        """Ground truth is based on generator, independent of detector outputs."""
        gt = self.bench.build_ground_truth()
        # Should be deterministic
        gt2 = self.bench.build_ground_truth()
        self.assertEqual(gt, gt2)


if __name__ == "__main__":
    unittest.main()
