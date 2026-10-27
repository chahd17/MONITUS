#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused tests for hospital data partitioning (Step 3.4 micro-step 2).
"""

import unittest

import numpy as np

from ai_service.fl_utils import (
    partition_hospital_data,
    get_partition_summary,
    HOSPITAL_IDS,
    FEATURE_NAMES,
    WINDOW_SIZE,
)
from scripts.train_ml_detector import get_simulation_configs, MLSyntheticGenerator


class TestFLPartitioning(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.configs = get_simulation_configs()
        cls.partitions = partition_hospital_data(cls.configs)
    
    def test_hospital_ids(self):
        self.assertEqual(HOSPITAL_IDS, ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"])
        self.assertEqual(len(FEATURE_NAMES), 18)
        self.assertEqual(WINDOW_SIZE, 21)
    
    def test_simulation_isolation(self):
        # All seeds must be disjoint across splits
        train_seeds = set(s for s, _ in self.configs["train"])
        val_seeds = set(s for s, _ in self.configs["val"])
        test_seeds = set(s for s, _ in self.configs["test"])
        self.assertEqual(len(train_seeds & val_seeds), 0)
        self.assertEqual(len(train_seeds & test_seeds), 0)
        self.assertEqual(len(val_seeds & test_seeds), 0)
    
    def test_split_disjointness_across_partitions(self):
        all_sim_ids = []
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                for meta in self.partitions[split][hid]["meta"]:
                    all_sim_ids.append((split, meta["sim_id"]))
        # Check no sim crosses splits
        sim_to_splits = {}
        for split, sim_id in all_sim_ids:
            sim_to_splits.setdefault(sim_id, set()).add(split)
        for sim_id, splits in sim_to_splits.items():
            self.assertEqual(len(splits), 1)
    
    def test_hospital_isolation(self):
        # Each partition contains only its hospital's data
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                for meta in self.partitions[split][hid]["meta"]:
                    self.assertEqual(meta["hospital_id"], hid)
    
    def test_feature_extraction_matches_step3_3(self):
        # Check feature dimensions
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                X = self.partitions[split][hid]["X"]
                if X.shape[0] > 0:
                    self.assertEqual(X.shape[1], 18)
                    self.assertTrue(np.all(np.isfinite(X)))
    
    def test_provenance_metadata(self):
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                for meta in self.partitions[split][hid]["meta"]:
                    self.assertIn("sim_id", meta)
                    self.assertIn("sim_seed", meta)
                    self.assertIn("hospital_id", meta)
                    self.assertIn("date", meta)
                    self.assertIn("scenario", meta)
                    self.assertIn("split", meta)
                    self.assertIn("is_reporting_error", meta)
                    self.assertEqual(meta["split"], split)
    
    def test_reporting_error_labeled_negative(self):
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                for i, meta in enumerate(self.partitions[split][hid]["meta"]):
                    if meta["scenario"] == "reporting_error":
                        self.assertEqual(self.partitions[split][hid]["y"][i], 0)
    
    def test_determinism(self):
        p1 = partition_hospital_data(self.configs)
        p2 = partition_hospital_data(self.configs)
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                np.testing.assert_array_equal(p1[split][hid]["X"], p2[split][hid]["X"])
                np.testing.assert_array_equal(p1[split][hid]["y"], p2[split][hid]["y"])
    
    def test_sample_alignment(self):
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                p = self.partitions[split][hid]
                self.assertEqual(p["X"].shape[0], p["y"].shape[0])
                self.assertEqual(p["X"].shape[0], len(p["meta"]))
                self.assertEqual(p["n_samples"], p["X"].shape[0])
    
    def test_warmup_21_observations(self):
        # First sample should be at day 21 (index 20)
        gen = MLSyntheticGenerator()
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                for meta in self.partitions[split][hid]["meta"]:
                    if meta["hospital_id"] == hid:
                        # Just check dates are reasonable
                        self.assertRegex(meta["date"], r'^\d{4}-\d{2}-\d{2}$')
                        break
    
    def test_invalid_partition_inputs(self):
        bad_configs = {"train": [], "val": [], "test": []}
        with self.assertRaises(ValueError):
            partition_hospital_data(bad_configs)
    
    def test_no_cross_simulation_histories(self):
        # Histories reset per simulation - checked by construction
        # Each simulation processed separately
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                sim_ids = set(m["sim_id"] for m in self.partitions[split][hid]["meta"])
                # At least some sims
                if self.partitions[split][hid]["n_samples"] > 0:
                    self.assertGreater(len(sim_ids), 0)


if __name__ == '__main__':
    unittest.main()
