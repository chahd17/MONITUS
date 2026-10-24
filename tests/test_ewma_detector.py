#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the independent EWMA challenger detector.
Uses unittest and the Python standard library only.
"""

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.ewma_detector import EWMADetector


def make_observations(values, hospital_id="HOSP_TEST", city="Test"):
    """Build observation dicts from a list of case counts."""
    start = date(2024, 1, 1)
    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "hospital_id": hospital_id,
            "city": city,
            "respiratory_cases": str(v),
            "scenario": "test",
        }
        for i, v in enumerate(values)
    ]


class TestEWMADetector(unittest.TestCase):
    """Test cases for EWMADetector."""

    def setUp(self):
        self.detector = EWMADetector(alpha=0.2, initial_window=21, threshold=3.0)
        self.data_dir = project_root / "data" / "synthetic"

    # ---------------------------------------------------------------- setup
    def test_invalid_parameters(self):
        """Invalid constructor parameters must raise ValueError."""
        with self.assertRaises(ValueError):
            EWMADetector(alpha=0.0)
        with self.assertRaises(ValueError):
            EWMADetector(alpha=1.5)
        with self.assertRaises(ValueError):
            EWMADetector(initial_window=1)
        with self.assertRaises(ValueError):
            EWMADetector(threshold=0)
        with self.assertRaises(ValueError):
            EWMADetector(min_scale=0)

    def test_no_alerts_before_enough_history(self):
        """No result (and no alert) before initial_window + 1 observations."""
        for n in [0, 1, 10, 20, 21]:
            observations = make_observations([10] * n)
            results = self.detector.detect_anomalies_for_hospital(observations)
            self.assertEqual(results, [], f"Expected no results for n={n}")

    def test_first_scored_day_is_initial_window(self):
        """Scoring starts exactly at index initial_window (the 22nd day)."""
        observations = make_observations([10] * 21 + [50])
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], observations[21]["date"])
        self.assertEqual(results[0]["observed_cases"], 50)

    def test_initialization_expected_value(self):
        """The first expected_cases equals the mean of the 21-day seed."""
        seed = [10, 12, 14] * 7  # 21 values, mean = 12
        observations = make_observations(seed + [12])
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertAlmostEqual(results[0]["expected_cases"], 12.0, places=4)

    # ------------------------------------------------------------ causality
    def test_no_future_data_leakage(self):
        """Changing future values must not alter earlier results."""
        base = [10] * 21 + [10, 10, 10, 10, 10]
        changed = list(base)
        changed[-1] = 999  # modify the last (future) observation

        results_base = self.detector.detect_anomalies_for_hospital(make_observations(base))
        results_changed = self.detector.detect_anomalies_for_hospital(make_observations(changed))

        # Every earlier result must be identical; only the last differs.
        self.assertEqual(len(results_base), len(results_changed))
        for a, b in zip(results_base[:-1], results_changed[:-1]):
            self.assertEqual(a, b)
        self.assertNotEqual(results_base[-1], results_changed[-1])

    def test_current_value_scored_before_update(self):
        """A huge current value is scored against the prior baseline, not itself."""
        observations = make_observations([10] * 21 + [1000])
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertEqual(results[0]["expected_cases"], 10.0)
        self.assertGreater(results[0]["anomaly_score"], 100)
        self.assertTrue(results[0]["anomaly_flag"])

    # ---------------------------------------------------------- EWMA update
    def test_ewma_update_formula(self):
        """expected_{t+1} = alpha * x_t + (1 - alpha) * expected_t."""
        observations = make_observations([10] * 21 + [20, 30])
        results = self.detector.detect_anomalies_for_hospital(observations)

        # Day 22 scored against 10, then mean becomes 0.2*20 + 0.8*10 = 12
        self.assertAlmostEqual(results[0]["expected_cases"], 10.0, places=4)
        self.assertAlmostEqual(results[1]["expected_cases"], 12.0, places=4)

        # Day 23 scored against 12, then mean becomes 0.2*30 + 0.8*12 = 15.6
        deep = EWMADetector(alpha=0.2, initial_window=21, threshold=3.0)
        extended = deep.detect_anomalies_for_hospital(
            make_observations([10] * 21 + [20, 30, 40])
        )
        self.assertAlmostEqual(extended[2]["expected_cases"], 15.6, places=4)

    def test_alpha_one_tracks_current_value(self):
        """With alpha=1 the baseline equals the previous observation."""
        detector = EWMADetector(alpha=1.0, initial_window=21, threshold=3.0)
        observations = make_observations([10] * 21 + [20, 30])
        results = detector.detect_anomalies_for_hospital(observations)
        self.assertAlmostEqual(results[0]["expected_cases"], 10.0, places=4)
        self.assertAlmostEqual(results[1]["expected_cases"], 20.0, places=4)

    # ------------------------------------------------------- one-sided flags
    def test_only_positive_increases_flagged(self):
        """Large decreases must not be flagged (one-sided detector)."""
        observations = make_observations([50] * 21 + [1])
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertLess(results[0]["anomaly_score"], 0)
        self.assertFalse(results[0]["anomaly_flag"])

    def test_spike_flagged(self):
        """An abrupt increase well above the baseline is flagged."""
        observations = make_observations([10] * 21 + [100])
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertTrue(results[0]["anomaly_flag"])

    def test_flag_respects_threshold_margin(self):
        """Scores below/at the threshold are not flagged; above are."""
        observations = make_observations([10] * 21 + [15])
        results = self.detector.detect_anomalies_for_hospital(observations)
        # Constant history => scale floored at 1.0 => score 5 > 3 => flagged.
        self.assertTrue(results[0]["anomaly_flag"])
        self.assertTrue(results[0]["scale_fallback_used"])

        # A detector with a very high threshold flags nothing.
        strict = EWMADetector(alpha=0.2, initial_window=21, threshold=1000)
        strict_results = strict.detect_anomalies_for_hospital(observations)
        self.assertFalse(strict_results[0]["anomaly_flag"])

    def test_zero_variance_handling(self):
        """Constant history yields a floored scale and no division by zero."""
        observations = make_observations([7] * 30)
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertTrue(len(results) > 0)
        for r in results:
            self.assertGreaterEqual(r["scale_estimate"], self.detector.min_scale)
            self.assertTrue(r["scale_fallback_used"])
            self.assertEqual(r["anomaly_score"], 0.0)
            self.assertFalse(r["anomaly_flag"])

    # --------------------------------------------------------------- outputs
    def test_output_structure(self):
        """Each result exposes the documented stable fields."""
        observations = make_observations([10] * 21 + [20, 30])
        results = self.detector.detect_anomalies_for_hospital(observations)
        required = [
            "date", "hospital_id", "city", "observed_cases", "expected_cases",
            "scale_estimate", "anomaly_score", "anomaly_flag",
            "scale_fallback_used", "alpha",
        ]
        for r in results:
            for field in required:
                self.assertIn(field, r, f"Missing field {field}")
            self.assertIsInstance(r["anomaly_flag"], bool)
            self.assertIsInstance(r["observed_cases"], int)

    def test_analyze_file_is_deterministic(self):
        """Repeated runs on the same CSV produce identical results/counts."""
        csv_path = self.data_dir / "normal.csv"
        first = self.detector.analyze_file(csv_path)
        second = self.detector.analyze_file(csv_path)
        self.assertEqual(first, second)
        self.assertEqual(sorted(first.keys()), ["HOSP_SFX", "HOSP_SOU", "HOSP_TUN"])
        for hid in first:
            self.assertEqual(len(first[hid]), 69)  # 90 - 21 warm-up days

    def test_scenario_counts_stable(self):
        """Known synthetic counts for the EWMA challenger (regression check)."""
        expected_anomalies = {
            "normal": {"HOSP_TUN": 0, "HOSP_SOU": 0, "HOSP_SFX": 0},
            "regional_outbreak": {"HOSP_TUN": 1, "HOSP_SOU": 1, "HOSP_SFX": 0},
            "reporting_error": {"HOSP_TUN": 1, "HOSP_SOU": 0, "HOSP_SFX": 0},
        }
        for scenario, expected in expected_anomalies.items():
            results = self.detector.analyze_file(self.data_dir / f"{scenario}.csv")
            actual = {
                hid: sum(1 for r in res if r["anomaly_flag"])
                for hid, res in results.items()
            }
            self.assertEqual(actual, expected, f"Unexpected counts for {scenario}")

    def test_normal_and_spike_days(self):
        """Verify the exact flagged dates for known scenarios."""
        outbreak = self.detector.analyze_file(self.data_dir / "regional_outbreak.csv")
        flagged = {
            hid: [r["date"] for r in res if r["anomaly_flag"]]
            for hid, res in outbreak.items()
        }
        self.assertEqual(flagged["HOSP_TUN"], ["2024-03-17"])
        self.assertEqual(flagged["HOSP_SOU"], ["2024-03-17"])
        self.assertEqual(flagged["HOSP_SFX"], [])

        reporting = self.detector.analyze_file(self.data_dir / "reporting_error.csv")
        flagged_reporting = [
            r["date"] for r in reporting["HOSP_TUN"] if r["anomaly_flag"]
        ]
        self.assertEqual(flagged_reporting, ["2024-02-28"])


if __name__ == "__main__":
    unittest.main()
