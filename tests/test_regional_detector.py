#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for regional corroboration detector.
Uses unittest, standard library only.
"""

import unittest
from datetime import date, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.anomaly_detector import AnomalyDetector
from ai_service.regional_detector import RegionalDetector


class TestRegionalDetector(unittest.TestCase):
    """Test cases for RegionalDetector."""
    
    def setUp(self):
        self.detector = AnomalyDetector(window_size=21, threshold=3.5)
        self.regional = RegionalDetector(min_supporting_hospitals=2)
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "synthetic"
    
    def test_normal_data_no_regional_signals(self):
        """Test normal data produces no regional signals."""
        csv_path = self.data_dir / "normal.csv"
        regional_reports = self.regional.analyze_file(csv_path, self.detector)
        regional_signals = [r for r in regional_reports if r['regional_signal']]
        self.assertEqual(len(regional_signals), 0, "Normal data should have no regional signals")
    
    def test_simultaneous_anomalies_two_sites(self):
        """Test simultaneous anomalies at 2 sites create regional signal."""
        # Create individual results with same date anomalies at 2 hospitals
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ],
            'HOSP_SOU': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        reports = self.regional.corroborate(individual_results)
        self.assertEqual(len(reports), 1)
        self.assertTrue(reports[0]['regional_signal'])
        self.assertEqual(reports[0]['num_supporting_sites'], 2)
        self.assertEqual(set(reports[0]['supporting_hospitals']), {'HOSP_TUN', 'HOSP_SOU'})
    
    def test_anomalies_different_dates_no_regional(self):
        """Test anomalies at different dates do not create regional signal."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ],
            'HOSP_SOU': [
                {'date': '2024-03-02', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        reports = self.regional.corroborate(individual_results)
        # Each date has only 1 hospital
        self.assertEqual(len(reports), 2)
        for r in reports:
            self.assertFalse(r['regional_signal'])
            self.assertEqual(r['num_supporting_sites'], 1)
    
    def test_one_site_reporting_error(self):
        """Test one-site reporting error does not create regional signal."""
        csv_path = self.data_dir / "reporting_error.csv"
        regional_reports = self.regional.analyze_file(csv_path, self.detector)
        regional_signals = [r for r in regional_reports if r['regional_signal']]
        # Should have no regional signals (only 1 hospital affected)
        self.assertEqual(len(regional_signals), 0, "One-site anomaly should not create regional signal")
    
    def test_duplicate_sites_rejected(self):
        """Test duplicate hospital/date records are handled."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0},
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.1, 'observed_cases': 51,
                 'baseline_median': 15.0, 'mad': 1.0}  # duplicate
            ],
            'HOSP_SOU': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        reports = self.regional.corroborate(individual_results)
        self.assertEqual(len(reports), 1)
        self.assertTrue(reports[0]['regional_signal'])
        self.assertEqual(reports[0]['num_supporting_sites'], 2)  # Still only 2 distinct hospitals
    
    def test_missing_observations_handled(self):
        """Test missing dates and missing hospital observations don't interpret as zero."""
        # Hospital with no data for a date
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ]
            # HOSP_SOU has no observations at all
        }
        reports = self.regional.corroborate(individual_results)
        # Only 1 hospital, no regional signal
        self.assertEqual(len(reports), 1)
        self.assertFalse(reports[0]['regional_signal'])
        self.assertEqual(reports[0]['num_supporting_sites'], 1)
    
    def test_configurable_quorum(self):
        """Test configurable minimum supporting hospitals."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ],
            'HOSP_SOU': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0}
            ],
            'HOSP_SFX': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SFX', 'city': 'Sfax',
                 'anomaly_flag': True, 'anomaly_score': 4.8, 'observed_cases': 48,
                 'baseline_median': 15.0, 'mad': 1.0}
            ]
        }
        # Default quorum 2
        regional2 = RegionalDetector(min_supporting_hospitals=2)
        reports2 = regional2.corroborate(individual_results)
        self.assertTrue(reports2[0]['regional_signal'])
        # Quorum 3
        regional3 = RegionalDetector(min_supporting_hospitals=3)
        reports3 = regional3.corroborate(individual_results)
        self.assertTrue(reports3[0]['regional_signal'])
        # Quorum 4
        regional4 = RegionalDetector(min_supporting_hospitals=4)
        reports4 = regional4.corroborate(individual_results)
        self.assertFalse(reports4[0]['regional_signal'])
    
    def test_report_structure(self):
        """Test regional report structure."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ]
        }
        reports = self.regional.corroborate(individual_results)
        r = reports[0]
        required = ['date', 'supporting_hospitals', 'individual_anomaly_scores',
                   'num_supporting_sites', 'regional_signal', 'explanatory_reason']
        for field in required:
            self.assertIn(field, r)


if __name__ == "__main__":
    unittest.main()
