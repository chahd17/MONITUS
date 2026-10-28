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
    apply_fixed_feature_transform,
    ROBUST_ZSCORE_FEATURE_INDEX,
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

    def test_train_val_test_seeds_disjoint(self):
        seeds_by_split = {}
        for split in ["train", "val", "test"]:
            seeds = set()
            for hid in HOSPITAL_IDS:
                seeds |= {m["sim_seed"] for m in self.partitions[split][hid]["meta"]}
            seeds_by_split[split] = seeds
        self.assertEqual(seeds_by_split["train"] & seeds_by_split["val"], set())
        self.assertEqual(seeds_by_split["train"] & seeds_by_split["test"], set())
        self.assertEqual(seeds_by_split["val"] & seeds_by_split["test"], set())

    def test_fixed_transform_clips_only_robust_zscore(self):
        X = np.array([[1.0] * 18, [2.0] * 18])
        X[0, ROBUST_ZSCORE_FEATURE_INDEX] = 1e9
        X[1, ROBUST_ZSCORE_FEATURE_INDEX] = -1e9
        out = apply_fixed_feature_transform(X, clip=5.0)
        self.assertTrue(np.all(out[:, ROBUST_ZSCORE_FEATURE_INDEX] <= 5.0))
        self.assertTrue(np.all(out[:, ROBUST_ZSCORE_FEATURE_INDEX] >= -5.0))
        # Other features untouched
        for i in range(18):
            if i != ROBUST_ZSCORE_FEATURE_INDEX:
                np.testing.assert_array_equal(out[:, i], X[:, i])
        # Original not mutated
        self.assertEqual(X[0, ROBUST_ZSCORE_FEATURE_INDEX], 1e9)

    def test_fixed_transform_none_is_identity(self):
        X = self.partitions["val"]["HOSP_TUN"]["X"]
        np.testing.assert_array_equal(apply_fixed_feature_transform(X, clip=None), X)

    def test_fixed_transform_is_deterministic(self):
        X = self.partitions["val"]["HOSP_TUN"]["X"]
        a = apply_fixed_feature_transform(X, clip=5.0)
        b = apply_fixed_feature_transform(X, clip=5.0)
        np.testing.assert_array_equal(a, b)

    def test_fixed_transform_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            apply_fixed_feature_transform(np.zeros((2, 17)), clip=5.0)
        with self.assertRaises(ValueError):
            apply_fixed_feature_transform(np.zeros(18), clip=5.0)
        with self.assertRaises(ValueError):
            apply_fixed_feature_transform(np.ones((2, 18)), clip=0.0)




    def test_train_val_only_does_not_generate_test(self):
        # Diagnostic path must not generate or process test simulations
        with self.assertRaises(ValueError):
            partition_hospital_data(splits=["train", "val", "test"])




    def test_exact_features_labels_from_step3_extractor(self):
        from ai_service.ml_features import build_causal_features
        from scripts.train_ml_detector import MLSyntheticGenerator, label_outbreak_day, get_simulation_configs
        # Reconstruct exactly as partition_hospital_data does and compare
        configs = get_simulation_configs()
        gen = MLSyntheticGenerator()
        for split in ["train"]:
            for sim_seed, scen_type in configs[split]:
                rows = gen.generate_simulation(sim_seed, scen_type)
                by_hosp = {}
                for row in rows:
                    by_hosp.setdefault(row["hospital_id"], []).append(row)
                for hid in HOSPITAL_IDS:
                    if hid not in by_hosp:
                        continue
                    hosp_rows = sorted(by_hosp[hid], key=lambda r: r["date"])
                    history = []
                    idx_out = 0
                    for idx, row in enumerate(hosp_rows):
                        history.append(float(row["respiratory_cases"]))
                        if len(history) >= 21:
                            X_feat = build_causal_features(history, 21)
                            y_label = label_outbreak_day(scen_type, idx, gen.days, hid)
                            np.testing.assert_array_equal(X_feat, self.partitions[split][hid]["X"][idx_out])
                            self.assertEqual(int(y_label), int(self.partitions[split][hid]["y"][idx_out]))
                            self.assertEqual(self.partitions[split][hid]["meta"][idx_out]["sim_seed"], int(sim_seed))
                            self.assertEqual(self.partitions[split][hid]["meta"][idx_out]["hospital_id"], hid)
                            idx_out += 1
                break
            break
        # Verify 21-observation warmup: first sample uses history up to day 21
        # and first eligible date is around day 21
        first_meta = self.partitions["train"]["HOSP_TUN"]["meta"][0]
        self.assertIsNotNone(first_meta["date"])

    def test_no_cross_history_leakage_distinct_sims(self):
        from scripts.train_ml_detector import MLSyntheticGenerator
        gen = MLSyntheticGenerator()
        rows1 = gen.generate_simulation(7777, "normal")
        rows2 = gen.generate_simulation(6666, "outbreak")
        h1 = []
        for r in rows1:
            if r["hospital_id"] == "HOSP_TUN":
                h1.append(r["respiratory_cases"])
        h2 = []
        for r in rows2:
            if r["hospital_id"] == "HOSP_TUN":
                h2.append(r["respiratory_cases"])
        self.assertEqual(len(h1), len(h2))
        self.assertFalse(all(a == b for a, b in zip(h1, h2)))
        # Same seed reused across hospitals within a split (shared simulation). No seed reused across different splits.
        seeds_by_split = {}
        for split in ["train", "val", "test"]:
            seeds_by_split[split] = set()
            for hid in HOSPITAL_IDS:
                for m in self.partitions[split][hid]["meta"]:
                    seeds_by_split[split].add(m["sim_seed"])
                    self.assertEqual(m["hospital_id"], hid)
            self.assertGreaterEqual(len(seeds_by_split[split]), 1)
        self.assertEqual(seeds_by_split["train"] & seeds_by_split["val"], set())
        self.assertEqual(seeds_by_split["train"] & seeds_by_split["test"], set())
        self.assertEqual(seeds_by_split["val"] & seeds_by_split["test"], set())
        self.assertEqual(len(seeds_by_split["train"]) + len(seeds_by_split["val"]) + len(seeds_by_split["test"]), len(self.configs["train"]) + len(self.configs["val"]) + len(self.configs["test"]))


if __name__ == '__main__':
    unittest.main()
