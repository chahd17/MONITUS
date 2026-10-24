#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for FastAPI surveillance API.
Uses TestClient, standard library + fastapi.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from ai_service.api import app


class TestSurveillanceAPI(unittest.TestCase):
    """Test cases for surveillance API."""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_health(self):
        """Test health endpoint."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["synthetic_only"])
        self.assertFalse(data.get("confirmed_outbreak", True))
    
    def test_scenarios(self):
        """Test scenarios endpoint."""
        response = self.client.get("/api/v1/scenarios")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("normal", data["permitted_scenarios"])
        self.assertIn("regional_outbreak", data["permitted_scenarios"])
        self.assertIn("reporting_error", data["permitted_scenarios"])
        self.assertTrue(data["synthetic_only"])
    
    def test_summary_normal(self):
        """Test summary for normal scenario."""
        response = self.client.get("/api/v1/surveillance/summary?scenario=normal")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario"], "normal")
        self.assertTrue(data["synthetic_only"])
        self.assertFalse(data["confirmed_outbreak"])
        self.assertIsInstance(data["hospitals"], list)
        self.assertEqual(len(data["hospitals"]), 3)
        self.assertIsInstance(data["regional_signal_dates"], list)
    
    def test_summary_regional_outbreak(self):
        """Test summary for regional_outbreak scenario."""
        response = self.client.get("/api/v1/surveillance/summary?scenario=regional_outbreak")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario"], "regional_outbreak")
        self.assertTrue(data["synthetic_only"])
        self.assertFalse(data["confirmed_outbreak"])
        self.assertGreater(len(data["regional_signal_dates"]), 0)
    
    def test_summary_reporting_error(self):
        """Test summary for reporting_error scenario."""
        response = self.client.get("/api/v1/surveillance/summary?scenario=reporting_error")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["synthetic_only"])
        self.assertFalse(data["confirmed_outbreak"])
    
    def test_alerts_all_scenarios(self):
        """Test alerts endpoint for all scenarios."""
        for scenario in ["normal", "regional_outbreak", "reporting_error"]:
            response = self.client.get(f"/api/v1/surveillance/alerts?scenario={scenario}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["scenario"], scenario)
            self.assertTrue(data["synthetic_only"])
            self.assertFalse(data["confirmed_outbreak"])
            self.assertIsInstance(data["alerts"], list)
    
    def test_hospitals_all_scenarios(self):
        """Test hospitals endpoint for all scenarios."""
        for scenario in ["normal", "regional_outbreak", "reporting_error"]:
            response = self.client.get(f"/api/v1/surveillance/hospitals?scenario={scenario}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["scenario"], scenario)
            self.assertTrue(data["synthetic_only"])
            self.assertFalse(data["confirmed_outbreak"])
            self.assertEqual(len(data["hospitals"]), 3)
            for h in data["hospitals"]:
                self.assertIn(h["hospital_id"], ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"])
                self.assertIsInstance(h["anomalies"], list)
    
    def test_invalid_scenario(self):
        """Test invalid scenario returns 422."""
        response = self.client.get("/api/v1/surveillance/summary?scenario=invalid")
        self.assertEqual(response.status_code, 422)
    
    def test_missing_scenario(self):
        """Test missing scenario parameter."""
        response = self.client.get("/api/v1/surveillance/summary")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
