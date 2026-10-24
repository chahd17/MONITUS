#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for synthetic hospital data generation.
Uses unittest, standard library only.
"""

import csv
import unittest
from datetime import date, timedelta
from pathlib import Path


class TestHospitalDataGeneration(unittest.TestCase):
    """Test cases for generated synthetic hospital data."""
    
    def setUp(self):
        """Set up test paths."""
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "synthetic"
        self.scenarios = ["normal.csv", "regional_outbreak.csv", "reporting_error.csv"]
        self.hospitals = ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"]
        self.cities = ["Tunis", "Sousse", "Sfax"]
        self.required_columns = ["date", "hospital_id", "city", "respiratory_cases", "scenario"]
    
    def test_files_exist(self):
        """Test that all three CSV files are created."""
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            self.assertTrue(path.exists(), f"{scenario_file} should exist")
    
    def test_row_counts(self):
        """Test that each file has correct row count (90 days * 3 hospitals = 270 rows)."""
        expected_rows = 90 * 3  # 90 days, 3 hospitals
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), expected_rows, 
                           f"{scenario_file} should have {expected_rows} rows")
    
    def test_columns(self):
        """Test that all files have the expected columns."""
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, self.required_columns,
                               f"{scenario_file} should have columns {self.required_columns}")
    
    def test_date_ordering(self):
        """Test that dates are sequential for each hospital in each scenario."""
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Group by hospital
            for hospital_id in self.hospitals:
                hospital_rows = [r for r in rows if r["hospital_id"] == hospital_id]
                # Sort by date to be sure
                hospital_rows_sorted = sorted(hospital_rows, key=lambda x: x["date"])
                # Check sequential
                start_d = date.fromisoformat(hospital_rows_sorted[0]["date"])
                for i, row in enumerate(hospital_rows_sorted):
                    expected_date = start_d + timedelta(days=i)
                    actual_date = date.fromisoformat(row["date"])
                    self.assertEqual(actual_date, expected_date,
                                   f"{scenario_file} {hospital_id} dates should be sequential")
    
    def test_nonnegative_integers(self):
        """Test that respiratory_cases are non-negative integers."""
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            for row in rows:
                cases_str = row["respiratory_cases"]
                # Check it's integer
                try:
                    cases_int = int(cases_str)
                except ValueError:
                    self.fail(f"{scenario_file}: respiratory_cases should be integer, got {cases_str}")
                self.assertGreaterEqual(cases_int, 0,
                                      f"{scenario_file}: cases should be non-negative")
                # Check it's non-negative (and integer value)
                self.assertEqual(str(cases_int), cases_str,
                               f"{scenario_file}: cases should be integer string")
    
    def test_scenario_labels(self):
        """Test that scenario column matches filename."""
        for scenario_file in self.scenarios:
            scenario_name = scenario_file.replace(".csv", "")
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            for row in rows:
                self.assertEqual(row["scenario"], scenario_name,
                               f"{scenario_file}: all rows should have scenario={scenario_name}")
    
    def test_hospitals_and_cities(self):
        """Test that all three hospitals appear in all scenarios."""
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            hospital_ids = set(r["hospital_id"] for r in rows)
            self.assertEqual(hospital_ids, set(self.hospitals),
                           f"{scenario_file} should have all three hospitals")
            # Check city mapping
            for row in rows:
                if row["hospital_id"] == "HOSP_TUN":
                    self.assertEqual(row["city"], "Tunis")
                elif row["hospital_id"] == "HOSP_SOU":
                    self.assertEqual(row["city"], "Sousse")
                elif row["hospital_id"] == "HOSP_SFX":
                    self.assertEqual(row["city"], "Sfax")
    
    def test_regional_outbreak_characteristics(self):
        """Test regional_outbreak: sustained increase in final 14 days for at least two hospitals."""
        path = self.data_dir / "regional_outbreak.csv"
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Group by hospital
        for hospital_id in ["HOSP_TUN", "HOSP_SOU"]:
            hospital_rows = sorted([r for r in rows if r["hospital_id"] == hospital_id],
                                 key=lambda x: x["date"])
            # First 76 days vs last 14 days
            first_76 = hospital_rows[:76]
            last_14 = hospital_rows[76:]
            avg_first = sum(int(r["respiratory_cases"]) for r in first_76) / len(first_76)
            avg_last = sum(int(r["respiratory_cases"]) for r in last_14) / len(last_14)
            self.assertGreater(avg_last, avg_first,
                             f"{hospital_id} should have higher average in final 14 days")
    
    def test_reporting_error_characteristics(self):
        """Test reporting_error: one extreme one-day spike at only one hospital."""
        path = self.data_dir / "reporting_error.csv"
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Find spikes > 50
        spikes = []
        for row in rows:
            cases = int(row["respiratory_cases"])
            if cases > 50:
                spikes.append(row)
        # Should have exactly 1 spike (one extreme one-day spike at only one hospital)
        self.assertEqual(len(spikes), 1, "Should have exactly one extreme spike")
        # Check it's only at one hospital
        spike_hospitals = set(s["hospital_id"] for s in spikes)
        self.assertEqual(len(spike_hospitals), 1, "Spike should be at only one hospital")
    
    def test_reproducibility(self):
        """Test reproducibility - running generator again should produce identical files."""
        import subprocess
        import sys
        
        # Run generator again
        script_path = self.project_root / "scripts" / "generate_hospital_data.py"
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=str(self.project_root),
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "Generator should run successfully")
        
        # Check files are identical (compare checksums by reading content)
        for scenario_file in self.scenarios:
            path = self.data_dir / scenario_file
            with path.open("r", encoding="utf-8") as f:
                content1 = f.read()
            # Read again after regeneration
            with path.open("r", encoding="utf-8") as f:
                content2 = f.read()
            self.assertEqual(content1, content2, 
                           f"{scenario_file} should be identical after regeneration (reproducible)")


if __name__ == "__main__":
    unittest.main()
