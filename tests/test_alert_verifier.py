#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for alert verifier.
Uses unittest, standard library only.
"""

import unittest
from datetime import date, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.alert_verifier import AlertVerifier
from ai_service.anomaly_detector import AnomalyDetector
from ai_service.regional_detector import RegionalDetector


class TestAlertVerifier(unittest.TestCase):
    """Test cases for AlertVerifier."""
    
    def setUp(self):
        self.verifier = AlertVerifier(persistence_days=2, persistence_window=3)
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "synthetic"
    
    def test_normal_scenario(self):
        """Test normal data gives NORMAL or no assessments."""
        csv_path = self.data_dir / "normal.csv"
        assessments = self.verifier.analyze_scenario(csv_path)
        # Normal should have few or no concerning assessments
        for a in assessments:
            self.assertNotEqual(a['status'], "REGIONAL_SIGNAL_REQUIRES_REVIEW")
    
    def test_isolated_spike(self):
        """Test single-site isolated anomaly."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 65.0, 'observed_cases': 111,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0]['status'], "ISOLATED_ANOMALY")
        self.assertEqual(assessments[0]['num_supporting_sites'], 1)
        # Should have data quality warning for extremely unusual spike
        self.assertTrue(len(assessments[0]['data_quality_warnings']) > 0)
    
    def test_one_day_multi_site_signal_unconfirmed(self):
        """Test one-day multi-site signal without persistence."""
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
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        self.assertEqual(assessments[0]['status'], "REGIONAL_SIGNAL_UNCONFIRMED")
    
    def test_sustained_regional_pattern(self):
        """Test sustained regional pattern requires review."""
        individual_results = {
            'HOSP_TUN': [],
            'HOSP_SOU': []
        }
        # Create anomalies on 3 consecutive days for both hospitals
        for i in range(3):
            d = (date(2024, 3, 1) + timedelta(days=i)).isoformat()
            individual_results['HOSP_TUN'].append({
                'date': d, 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                'anomaly_flag': True, 'anomaly_score': 5.0 + i, 'observed_cases': 50,
                'baseline_median': 15.0, 'mad': 1.0
            })
            individual_results['HOSP_SOU'].append({
                'date': d, 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                'anomaly_flag': True, 'anomaly_score': 4.5 + i, 'observed_cases': 45,
                'baseline_median': 14.0, 'mad': 1.0
            })
        
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        # Third day should require review (2+ in 3-day window)
        self.assertEqual(assessments[-1]['status'], "REGIONAL_SIGNAL_REQUIRES_REVIEW")
    
    def test_gaps_in_observation_dates(self):
        """Test gaps in observation dates don't cause issues."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ],
            'HOSP_SOU': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0},
                # Gap on 03-02
                {'date': '2024-03-03', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.8, 'observed_cases': 46,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        # Should not crash, handles missing observations
        self.assertTrue(len(assessments) >= 1)
    
    def test_duplicate_observations(self):
        """Test duplicate observations are flagged."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0},
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.1, 'observed_cases': 51,
                 'baseline_median': 15.0, 'mad': 1.0}
            ],
            'HOSP_SOU': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
                 'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
                 'baseline_median': 14.0, 'mad': 1.0}
            ]
        }
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        # Should have data quality warning for duplicates
        warnings = assessments[0]['data_quality_warnings']
        self.assertTrue(any('duplicate' in w.lower() for w in warnings))
    
    def test_no_future_data_leakage(self):
        """Test verifier doesn't look ahead."""
        individual_results = {
            'HOSP_TUN': [],
            'HOSP_SOU': []
        }
        # Anomaly only on day 1, not on days 2,3
        individual_results['HOSP_TUN'].append({
            'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
            'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
            'baseline_median': 15.0, 'mad': 1.0
        })
        individual_results['HOSP_SOU'].append({
            'date': '2024-03-01', 'hospital_id': 'HOSP_SOU', 'city': 'Sousse',
            'anomaly_flag': True, 'anomaly_score': 4.5, 'observed_cases': 45,
            'baseline_median': 14.0, 'mad': 1.0
        })
        
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        # Only 1 day in window, should be unconfirmed
        self.assertEqual(assessments[0]['status'], "REGIONAL_SIGNAL_UNCONFIRMED")
    
    def test_assessment_structure(self):
        """Test assessment has required fields."""
        individual_results = {
            'HOSP_TUN': [
                {'date': '2024-03-01', 'hospital_id': 'HOSP_TUN', 'city': 'Tunis',
                 'anomaly_flag': True, 'anomaly_score': 5.0, 'observed_cases': 50,
                 'baseline_median': 15.0, 'mad': 1.0}
            ]
        }
        regional = RegionalDetector(min_supporting_hospitals=2)
        regional_reports = regional.corroborate(individual_results)
        assessments = self.verifier.verify(regional_reports, individual_results)
        a = assessments[0]
        required = ['date', 'status', 'supporting_hospitals', 'num_supporting_sites',
                   'explanation', 'evidence_dates', 'checks_passed', 'checks_failed',
                   'data_quality_warnings']
        for field in required:
            self.assertIn(field, a)


if __name__ == "__main__":
    unittest.main()
