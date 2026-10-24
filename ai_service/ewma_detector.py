#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent EWMA challenger detector for individual hospitals.

This module is a SECOND, independent detection method. It does NOT reuse the
Median/MAD scores produced by ``ai_service/anomaly_detector.py`` and it does not
import that module. It computes its own causal one-sided EWMA baseline and its
own causal variability estimate using only Python standard-library modules.

Method summary
--------------
For every hospital, the first ``initial_window`` days (default 21) are used only
to seed the baseline:

    expected_cases = arithmetic mean of the first N observations

and the initial scale is derived from the mean absolute deviation (MAD_abs)
around that initial mean. For normally distributed data,
``E[|x - mean|] = sigma * sqrt(2/pi)``, so ``sigma ~= 1.2533 * MAD_abs``. This
constant (``MAD_ABS_TO_SIGMA``) is the inverse of ``sqrt(2/pi)`` and is used to
put the absolute-deviation scale on a standard-deviation-like footing.

From day N+1 onward, for each observation x_t:

1. Score the observation against the baseline built from PRIOR days only:
       anomaly_score = (x_t - expected_t) / max(scale_t, MIN_SCALE)
2. Flag it if ``anomaly_score > threshold`` (one-sided: only unusual increases).
3. Update the running baseline (EWMA) AFTER scoring:
       expected_{t+1} = alpha * x_t + (1 - alpha) * expected_t
4. Update the causal scale estimate AFTER scoring, using the residual of the
   current observation against the PRE-UPDATE expectation:
       raw_scale_{t+1} = alpha * |x_t - expected_t| + (1 - alpha) * raw_scale_t
   ``raw_scale`` is kept in mean-absolute-deviation units and converted to a
   standard-deviation-like value (multiplied by 1.2533) at scoring time.

Zero / near-zero variability
----------------------------
If the initial history (or the running scale) produces a sigma-like scale
below ``MIN_SCALE`` (default 1.0), the scale is floored at ``MIN_SCALE``. This
avoids division by zero and prevents an artificially infinite score when
historical counts are perfectly flat. A ``scale_fallback_used`` flag is
reported so the behaviour stays visible and auditable.

The threshold is a configurable statistical flag level. It is NOT clinically
validated and does not confirm an outbreak.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple


class EWMADetector:
    """Causal one-sided EWMA detector for unusually high case counts."""

    # Inverse of sqrt(2/pi): converts mean absolute deviation to sigma-like scale
    MAD_ABS_TO_SIGMA = 1.2533141373155003
    # Minimum scale, used when variability is zero or near zero
    MIN_SCALE_FALLBACK = 1.0
    # Default smoothing factor
    DEFAULT_ALPHA = 0.2
    # Default initial history length
    DEFAULT_INITIAL_WINDOW = 21
    # Default flag threshold (statistical, NOT clinically validated)
    DEFAULT_THRESHOLD = 3.0

    def __init__(
        self,
        alpha: float = DEFAULT_ALPHA,
        initial_window: int = DEFAULT_INITIAL_WINDOW,
        threshold: float = DEFAULT_THRESHOLD,
        min_scale: float = MIN_SCALE_FALLBACK,
    ):
        """
        Initialize the EWMA detector.

        Args:
            alpha: EWMA smoothing factor in (0, 1]. Higher = faster adaptation.
            initial_window: Number of initial days used to seed baseline/scale.
            threshold: One-sided positive score threshold for anomaly_flag.
            min_scale: Floor applied to the scale estimate (zero-variance guard).

        Raises:
            ValueError: If parameters are outside sensible bounds.
        """
        if not (0.0 < alpha <= 1.0):
            raise ValueError("alpha must be in (0, 1]")
        if initial_window < 2:
            raise ValueError("initial_window must be >= 2")
        if threshold <= 0:
            raise ValueError("threshold must be > 0")
        if min_scale <= 0:
            raise ValueError("min_scale must be > 0")

        self.alpha = float(alpha)
        self.initial_window = int(initial_window)
        self.threshold = float(threshold)
        self.min_scale = float(min_scale)

    @staticmethod
    def _mean(values: List[float]) -> float:
        """Arithmetic mean, 0.0 for an empty list."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _mean_absolute_deviation(values: List[float], center: float) -> float:
        """Mean absolute deviation around a supplied center."""
        if not values:
            return 0.0
        return sum(abs(v - center) for v in values) / len(values)

    def _initial_scale(self, values: List[float], center: float) -> float:
        """Seed the raw (mean-absolute-deviation) scale from initial history."""
        return self._mean_absolute_deviation(values, center)

    def _effective_scale(self, raw_scale: float) -> Tuple[float, bool]:
        """
        Convert the raw mean-absolute-deviation scale to sigma-like units and
        floor it at ``min_scale``.

        Returns (effective_scale, fallback_used).
        """
        scaled = raw_scale * self.MAD_ABS_TO_SIGMA
        if scaled < self.min_scale:
            return self.min_scale, True
        return scaled, False

    def detect_anomalies_for_hospital(self, observations: List[Dict]) -> List[Dict]:
        """
        Run the causal EWMA detector for one hospital.

        ``observations`` must be sorted by date (oldest first). Scoring starts at
        index ``initial_window`` (the 22nd day with the default 21-day seed), so
        no alert can be produced before enough history exists. Only prior
        observations influence each score; the current value is scored before it
        updates the baseline.
        """
        results: List[Dict] = []
        if len(observations) <= self.initial_window:
            # Not enough history to seed the detector; no alerts.
            return results

        seed = observations[:self.initial_window]
        seed_values = [float(o['respiratory_cases']) for o in seed]
        expected = self._mean(seed_values)
        raw_scale = self._initial_scale(seed_values, expected)

        for i in range(self.initial_window, len(observations)):
            current = observations[i]
            observed = float(current['respiratory_cases'])
            current_date = current['date']

            # --- Score against PRIOR baseline only (no update yet) ---
            effective_scale, fallback_used = self._effective_scale(raw_scale)
            score = (observed - expected) / effective_scale
            is_anomaly = score > self.threshold

            results.append({
                'date': current_date,
                'hospital_id': current['hospital_id'],
                'city': current.get('city', ''),
                'observed_cases': int(observed),
                'expected_cases': round(expected, 4),
                'scale_estimate': round(effective_scale, 4),
                'anomaly_score': round(score, 4),
                'anomaly_flag': is_anomaly,
                'scale_fallback_used': fallback_used,
                'alpha': self.alpha,
            })

            # --- Causal updates AFTER scoring ---
            residual = abs(observed - expected)
            expected = self.alpha * observed + (1.0 - self.alpha) * expected
            raw_scale = self.alpha * residual + (1.0 - self.alpha) * raw_scale

        return results

    def load_csv(self, csv_path: Path) -> Dict[str, List[Dict]]:
        """Load a CSV and group rows by hospital_id, sorted by date."""
        hospitals_data: Dict[str, List[Dict]] = {}
        with Path(csv_path).open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hospitals_data.setdefault(row['hospital_id'], []).append(row)

        for hid in hospitals_data:
            hospitals_data[hid].sort(key=lambda x: x['date'])
        return hospitals_data

    def analyze_file(self, csv_path: Path) -> Dict[str, List[Dict]]:
        """Analyze all hospitals in a CSV, returning results per hospital."""
        hospitals_data = self.load_csv(csv_path)
        return {
            hid: self.detect_anomalies_for_hospital(observations)
            for hid, observations in hospitals_data.items()
        }


def print_summary(results_by_hospital: Dict[str, List[Dict]], scenario_name: str,
                  threshold: float, alpha: float):
    """Print a readable summary of EWMA results for one scenario."""
    print(f"\n{'=' * 70}")
    print(f"EWMA Challenger - Scenario: {scenario_name}")
    print(f"alpha={alpha}, threshold={threshold} (statistical, NOT clinically validated)")
    print(f"{'=' * 70}")

    for hid in sorted(results_by_hospital.keys()):
        results = results_by_hospital[hid]
        city = results[0]['city'] if results else hid
        anomalies = [r for r in results if r['anomaly_flag']]
        print(f"\n{city} ({hid}):")
        print(f"  Scored days: {len(results)} (after initial warm-up history)")
        print(f"  Anomalous days (score > {threshold}): {len(anomalies)}")
        for a in anomalies:
            print(f"    {a['date']}: cases={a['observed_cases']}, "
                  f"expected={a['expected_cases']}, scale={a['scale_estimate']}, "
                  f"score={a['anomaly_score']:.4f}")


def main():
    """CLI demo on the three synthetic scenarios."""
    detector = EWMADetector(alpha=0.2, initial_window=21, threshold=3.0)
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"

    for scenario_file in ["normal.csv", "regional_outbreak.csv", "reporting_error.csv"]:
        csv_path = data_dir / scenario_file
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            continue
        scenario_name = scenario_file.replace(".csv", "")
        results = detector.analyze_file(csv_path)
        print_summary(results, scenario_name, detector.threshold, detector.alpha)

    print(f"\n{'=' * 70}")
    print("Note: independent EWMA challenger on synthetic data only.")
    print("No outbreak is confirmed and the threshold is not clinically validated.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
