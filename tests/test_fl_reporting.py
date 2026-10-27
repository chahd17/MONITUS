#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused tests for the Step 3.4 evaluation reports and evaluation integrity.

These tests protect:
- report schema (v1 historical + v2 post-review),
- confusion-matrix / metric consistency,
- sample-count consistency,
- fresh-seed isolation and determinism of partitioning,
- the frozen-config guard (not selected on test).
"""

import json
import unittest
from pathlib import Path

import numpy as np

from ai_service.fl_utils import partition_hospital_data, HOSPITAL_IDS
from scripts.train_ml_detector import get_simulation_configs


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS = PROJECT_ROOT / "reports"
V1 = REPORTS / "fl_simulation.json"
V2 = REPORTS / "fl_simulation_v2.json"
FROZEN = REPORTS / "fl_frozen_config.json"


def _recompute(m):
    tp, tn, fp, fn = m["tp"], m["tn"], m["fp"], m["fn"]
    n = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return n, precision, recall, f1


class TestFLReporting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.v1 = json.loads(V1.read_text(encoding="utf-8")) if V1.exists() else None
        cls.v2 = json.loads(V2.read_text(encoding="utf-8")) if V2.exists() else None
        cls.frozen = json.loads(FROZEN.read_text(encoding="utf-8")) if FROZEN.exists() else None

    def test_v1_historical_report_preserved(self):
        self.assertIsNotNone(self.v1, "v1 report must be preserved")
        # v1's real, low-recall historical result must not be silently rewritten.
        g = self.v1["federated"]["global"]
        self.assertEqual((g["tp"], g["fn"]), (3, 53))
        self.assertEqual(g["n_samples"], 1260)

    def test_v1_declares_no_privacy_guarantee(self):
        self.assertIn("NO FORMAL PRIVACY GUARANTEE", self.v1["privacy_warning"])

    def test_v2_report_schema(self):
        self.assertIsNotNone(self.v2, "v2 report missing; run scripts/eval_federated_v2.py")
        for key in ["version", "disclosure", "seed_rule", "fresh_seeds", "metadata",
                    "privacy_warning", "clinical_warning", "partition_summary",
                    "convergence_history", "federated", "centralized",
                    "reporting_error_analysis", "limitations"]:
            self.assertIn(key, self.v2)
        self.assertEqual(self.v2["version"], "v2")
        self.assertTrue(self.v2["metadata"]["test_evaluated_once"])

    def test_v2_warnings(self):
        self.assertIn("NO FORMAL PRIVACY GUARANTEE", self.v2["privacy_warning"])
        self.assertIn("NO SECURE AGGREGATION", self.v2["privacy_warning"])
        self.assertIn("NOT READY FOR CLINICAL", self.v2["clinical_warning"])

    def test_v2_metric_consistency(self):
        for section in ["federated", "centralized"]:
            for scope, m in [("global", self.v2[section]["global"]),
                             *[(h, self.v2[section]["per_hospital"][h]) for h in HOSPITAL_IDS]]:
                n, p, r, f1 = _recompute(m)
                self.assertEqual(n, m["n_samples"], f"{section}/{scope} n mismatch")
                self.assertAlmostEqual(p, m["precision"], places=12)
                self.assertAlmostEqual(r, m["recall"], places=12)
                self.assertAlmostEqual(f1, m["f1"], places=12)

    def test_v2_sample_count_consistency(self):
        total = 0
        for h in HOSPITAL_IDS:
            p = self.v2["partition_summary"]["test"][h]
            self.assertEqual(p["n_pos"] + p["n_neg"], p["n_samples"])
            total += p["n_samples"]
        self.assertEqual(total, self.v2["federated"]["global"]["n_samples"])
        self.assertEqual(total, self.v2["centralized"]["global"]["n_samples"])

    def test_v2_fresh_seeds_disjoint_from_used_seeds(self):
        used = set()
        for _, cfg in get_simulation_configs().items():
            used |= {seed for seed, _ in cfg}
        fresh = set()
        seen = set()
        for split in ["train", "val", "test"]:
            seeds = {seed for seed, _ in self.v2["fresh_seeds"][split]}
            # No reuse inside fresh config
            self.assertEqual(len(seeds & seen), 0)
            seen |= seeds
            fresh |= seeds
        self.assertEqual(fresh & used, set(), "fresh seeds must not reuse v1/Step 3.3 seeds")
        # Fresh test must not reuse the already-consumed v1 test seeds.
        v1_test = {seed for seed, _ in get_simulation_configs()["test"]}
        fresh_test = {seed for seed, _ in self.v2["fresh_seeds"]["test"]}
        self.assertEqual(fresh_test & v1_test, set())

    def test_v2_discloses_post_review(self):
        self.assertIn("REVIEW", self.v2["disclosure"].upper())
        self.assertIn("v1", self.v2["historical_report"]["note"])

    def test_frozen_config_not_selected_on_test(self):
        self.assertIsNotNone(self.frozen)
        self.assertIs(self.frozen["selected_on_test"], False)
        self.assertIn("train", self.frozen["selection_data"].lower())
        self.assertIn("validation", self.frozen["selection_data"].lower())

    def test_partitioning_is_deterministic(self):
        a = partition_hospital_data(sim_configs_by_split=self.v2["fresh_seeds"])
        b = partition_hospital_data(sim_configs_by_split=self.v2["fresh_seeds"])
        for split in ["train", "val", "test"]:
            for h in HOSPITAL_IDS:
                np.testing.assert_array_equal(a[split][h]["X"], b[split][h]["X"])
                np.testing.assert_array_equal(a[split][h]["y"], b[split][h]["y"])
                self.assertEqual(a[split][h]["n_samples"], b[split][h]["n_samples"])

    def test_reported_partition_counts_match_regeneration(self):
        p = partition_hospital_data(sim_configs_by_split=self.v2["fresh_seeds"])
        for split in ["train", "val", "test"]:
            for h in HOSPITAL_IDS:
                self.assertEqual(
                    int(p[split][h]["n_samples"]),
                    self.v2["partition_summary"][split][h]["n_samples"],
                )


if __name__ == '__main__':
    unittest.main()
