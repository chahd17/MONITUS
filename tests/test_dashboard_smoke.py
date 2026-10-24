#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke tests for dashboard - verify imports and data processing without browser.
Uses unittest, standard library only.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDashboardSmoke(unittest.TestCase):
    """Smoke tests for dashboard functionality."""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "synthetic"
    
    def test_imports(self):
        """Test that all required modules can be imported."""
        try:
            from ai_service.anomaly_detector import AnomalyDetector
            from ai_service.regional_detector import RegionalDetector
            from ai_service.alert_verifier import AlertVerifier
            import pandas as pd
            import plotly
            import streamlit
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_dashboard_module_import(self):
        """Test dashboard module can be imported."""
        # Add demo to path
        demo_path = self.project_root / "demo"
        sys.path.insert(0, str(demo_path))
        try:
            # Just check file exists and is readable
            dashboard_file = demo_path / "dashboard.py"
            self.assertTrue(dashboard_file.exists())
            with dashboard_file.open('r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('streamlit', content.lower())
            self.assertIn('MONITUS', content)
            self.assertIn('SYNTHETIC', content)
        except Exception as e:
            self.fail(f"Dashboard module issue: {e}")
    
    def test_data_processing_normal(self):
        """Test data processing for normal scenario."""
        from ai_service.anomaly_detector import AnomalyDetector
        from ai_service.regional_detector import RegionalDetector
        from ai_service.alert_verifier import AlertVerifier
        
        csv_path = self.data_dir / "normal.csv"
        self.assertTrue(csv_path.exists())
        
        detector = AnomalyDetector(window_size=21, threshold=3.5)
        regional_detector = RegionalDetector(min_supporting_hospitals=2)
        verifier = AlertVerifier(persistence_days=2, persistence_window=3)
        
        individual_results = detector.analyze_file(csv_path)
        regional_reports = regional_detector.corroborate(individual_results)
        assessments = verifier.verify(regional_reports, individual_results)
        
        self.assertIsInstance(individual_results, dict)
        self.assertIsInstance(regional_reports, list)
        self.assertIsInstance(assessments, list)
    
    def test_data_processing_regional_outbreak(self):
        """Test data processing for regional_outbreak scenario."""
        from ai_service.anomaly_detector import AnomalyDetector
        from ai_service.regional_detector import RegionalDetector
        from ai_service.alert_verifier import AlertVerifier
        
        csv_path = self.data_dir / "regional_outbreak.csv"
        self.assertTrue(csv_path.exists())
        
        detector = AnomalyDetector(window_size=21, threshold=3.5)
        regional_detector = RegionalDetector(min_supporting_hospitals=2)
        verifier = AlertVerifier(persistence_days=2, persistence_window=3)
        
        individual_results = detector.analyze_file(csv_path)
        regional_reports = regional_detector.corroborate(individual_results)
        assessments = verifier.verify(regional_reports, individual_results)
        
        self.assertIsInstance(individual_results, dict)
        self.assertGreater(len(regional_reports), 0)
    
    def test_data_processing_reporting_error(self):
        """Test data processing for reporting_error scenario."""
        from ai_service.anomaly_detector import AnomalyDetector
        from ai_service.regional_detector import RegionalDetector
        from ai_service.alert_verifier import AlertVerifier
        
        csv_path = self.data_dir / "reporting_error.csv"
        self.assertTrue(csv_path.exists())
        
        detector = AnomalyDetector(window_size=21, threshold=3.5)
        regional_detector = RegionalDetector(min_supporting_hospitals=2)
        verifier = AlertVerifier(persistence_days=2, persistence_window=3)
        
        individual_results = detector.analyze_file(csv_path)
        regional_reports = regional_detector.corroborate(individual_results)
        assessments = verifier.verify(regional_reports, individual_results)
        
        self.assertIsInstance(individual_results, dict)
        self.assertIsInstance(assessments, list)


if __name__ == "__main__":
    unittest.main()
