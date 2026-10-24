#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for anomaly detector.
Uses unittest, standard library only.
"""

import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.anomaly_detector import AnomalyDetector


class TestAnomalyDetector(unittest.TestCase):
    """Test cases for AnomalyDetector."""
    
    def setUp(self):
        self.detector = AnomalyDetector(window_size=21, threshold=3.5)
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "synthetic"
    
    def test_median_odd(self):
        """Test median calculation with odd number of elements."""
        values = [1, 2, 3, 4, 5]
        self.assertEqual(self.detector.median(values), 3.0)
    
    def test_median_even(self):
        """Test median calculation with even number of elements."""
        values = [1, 2, 3, 4]
        self.assertEqual(self.detector.median(values), 2.5)
    
    def test_mad_calculation(self):
        """Test MAD calculation."""
        values = [1, 2, 3, 4, 5]
        med = self.detector.median(values)
        mad_val, fallback = self.detector.mad(values, med)
        # Deviations from median 3: [2,1,0,1,2], median of deviations is 1
        self.assertEqual(mad_val, 1.0)
        self.assertFalse(fallback)
    
    def test_mad_zero_fallback(self):
        """Test MAD=0 handling with documented fallback."""
        values = [5, 5, 5, 5, 5]
        med = self.detector.median(values)
        mad_val, fallback = self.detector.mad(values, med)
        self.assertTrue(fallback)  # Should use fallback
        self.assertEqual(mad_val, self.detector.MIN_SCALE_FALLBACK)
    
    def test_no_future_data_leakage(self):
        """Test that current day and future observations are not used."""
        # Create simple test data
        observations = []
        start = date(2024, 1, 1)
        # Create 30 days with known pattern
        for i in range(30):
            observations.append({
                'date': (start + timedelta(days=i)).isoformat(),
                'hospital_id': 'HOSP_TEST',
                'city': 'Test',
                'respiratory_cases': str(10),  # constant
                'scenario': 'test'
            })
        # Change day 25 to high value
        observations[25]['respiratory_cases'] = str(100)
        # Change day 26 to very high value
        observations[26]['respiratory_cases'] = str(200)
        
        results = self.detector.detect_anomalies_for_hospital(observations)
        # For day 25 (index 25, history is indices 4-24), history should be all 10s
        # So it should detect day 25 as anomaly
        day25_result = [r for r in results if r['date'] == observations[25]['date']][0]
        self.assertEqual(day25_result['baseline_median'], 10.0)
        # For day 26, history includes day 25 (value 100) - median of mostly 10s with one 100 is still 10
        day26_result = [r for r in results if r['date'] == observations[26]['date']][0]
        self.assertEqual(day26_result['baseline_median'], 10.0)  # Median remains 10
        # But day 26 itself is not in history for day 26's calculation - correct, no leakage
    
    def test_anomaly_score_calculation(self):
        """Test anomaly score formula."""
        observations = []
        start = date(2024, 1, 1)
        # 21 days of baseline = 10, day 22 = 20
        for i in range(22):
            val = 10 if i < 21 else 20
            observations.append({
                'date': (start + timedelta(days=i)).isoformat(),
                'hospital_id': 'HOSP_TEST',
                'city': 'Test',
                'respiratory_cases': str(val),
                'scenario': 'test'
            })
        results = self.detector.detect_anomalies_for_hospital(observations)
        # For the 22nd day (index 21), history is first 21 days all 10
        result = results[0]
        self.assertEqual(result['baseline_median'], 10.0)
        self.assertTrue(result['anomaly_score'] > 0)  # Positive score
    
    def test_only_positive_anomalies_flagged(self):
        """Test that only positive anomalies above threshold are flagged."""
        observations = []
        start = date(2024, 1, 1)
        # 21 days of baseline = 20, day 22 = 1 (much lower)
        for i in range(22):
            val = 20 if i < 21 else 1
            observations.append({
                'date': (start + timedelta(days=i)).isoformat(),
                'hospital_id': 'HOSP_TEST',
                'city': 'Test',
                'respiratory_cases': str(val),
                'scenario': 'test'
            })
        results = self.detector.detect_anomalies_for_hospital(observations)
        result = results[0]
        self.assertLess(result['anomaly_score'], 0)  # Negative score
        self.assertFalse(result['anomaly_flag'])  # Should not be flagged
    
    def test_normal_data_few_anomalies(self):
        """Test normal scenario has few or no anomalies."""
        csv_path = self.data_dir / "normal.csv"
        results = self.detector.analyze_file(csv_path)
        total_anomalies = sum(len([r for r in res if r['anomaly_flag']]) 
                             for res in results.values())
        # Normal data should have very few anomalies (ideally 0, but allow small number)
        self.assertLess(total_anomalies, 10, "Normal data should have few anomalies")
    
    def test_reporting_error_spike_detection(self):
        """Test that isolated spike in reporting_error is detected."""
        csv_path = self.data_dir / "reporting_error.csv"
        results = self.detector.analyze_file(csv_path)
        # Should detect anomaly at HOSP_TUN (where spike is)
        tun_results = results.get('HOSP_TUN', [])
        tun_anomalies = [r for r in tun_results if r['anomaly_flag']]
        self.assertGreater(len(tun_anomalies), 0, "Should detect spike in reporting error")
        # Should be detected as positive anomaly
        for anom in tun_anomalies:
            self.assertGreater(anom['anomaly_score'], 3.5)
    
    def test_output_structure(self):
        """Test output structure has all required fields."""
        csv_path = self.data_dir / "normal.csv"
        results = self.detector.analyze_file(csv_path)
        for hid, res_list in results.items():
            if res_list:
                r = res_list[0]
                required_fields = ['date', 'hospital_id', 'city', 'observed_cases',
                                 'baseline_median', 'mad', 'anomaly_score', 'anomaly_flag']
                for field in required_fields:
                    self.assertIn(field, r, f"Missing field {field}")
    
    def test_minimum_history_requirement(self):
        """Test that detector needs at least 22 observations (21 history + 1)."""
        observations = []
        start = date(2024, 1, 1)
        for i in range(21):  # Only 21 days
            observations.append({
                'date': (start + timedelta(days=i)).isoformat(),
                'hospital_id': 'HOSP_TEST',
                'city': 'Test',
                'respiratory_cases': str(10),
                'scenario': 'test'
            })
        results = self.detector.detect_anomalies_for_hospital(observations)
        self.assertEqual(len(results), 0, "Should not detect with insufficient history")


if __name__ == "__main__":
    unittest.main()
