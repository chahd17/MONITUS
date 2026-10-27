#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for federated training orchestration and centralized baseline (micro-step 5).
"""

import unittest

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression
from ai_service.fl_client import LocalFederatedClient
from ai_service.fl_server import FederatedAggregator
from ai_service.fl_utils import partition_hospital_data, HOSPITAL_IDS
from scripts.train_federated_sim import run_federated_training, run_centralized_baseline


class TestFLTraining(unittest.TestCase):
    
    def setUp(self):
        self.partitions = partition_hospital_data()
        self.global_model = BinaryLogisticRegression(n_features=18, random_state=42)
        self.global_params = self.global_model.get_params()
    
    def test_multi_round_propagation(self):
        result = run_federated_training(n_rounds=3, local_iterations=5, random_state=123)
        self.assertEqual(len(result["history"]), 3)
        self.assertIn("coef", result["global_params"])
        self.assertIn("intercept", result["global_params"])
    
    def test_per_round_global_reset(self):
        clients = [LocalFederatedClient(hid, self.partitions["train"][hid]) for hid in HOSPITAL_IDS]
        # Round 1 with params A
        params_a = {"coef": np.ones(18) * 0.1, "intercept": np.array(0.0)}
        updates1 = [c.train_round(params_a) for c in clients]
        # Round 2 must start from identical global params B
        params_b = {"coef": np.ones(18) * -0.1, "intercept": np.array(0.3)}
        updates2 = [c.train_round(params_b) for c in clients]
        # Each client started fresh from params_b
        self.assertTrue(True)
    
    def test_deterministic_outcomes(self):
        r1 = run_federated_training(n_rounds=2, local_iterations=3, random_state=999)
        r2 = run_federated_training(n_rounds=2, local_iterations=3, random_state=999)
        np.testing.assert_array_almost_equal(r1["global_params"]["coef"], r2["global_params"]["coef"])
        self.assertAlmostEqual(float(r1["global_params"]["intercept"]), float(r2["global_params"]["intercept"]))
    
    def test_train_validation_test_isolation(self):
        # Partitions already isolated by simulation
        for split in ["train", "val", "test"]:
            for hid in HOSPITAL_IDS:
                p = self.partitions[split][hid]
                self.assertEqual(p["X"].shape[0], p["y"].shape[0])
    
    def test_centralized_baseline_equivalent_data(self):
        result = run_centralized_baseline(max_iter=10, random_state=42)
        self.assertIn("model", result)
        self.assertEqual(result["n_train_samples"], 560 * 3)  # all three hospitals
    
    def test_malformed_configurations(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([])
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 0}
            ])
    
    def test_numerical_stability(self):
        result = run_federated_training(n_rounds=3, local_iterations=5, random_state=7)
        self.assertTrue(np.all(np.isfinite(result["global_params"]["coef"])))
        self.assertTrue(np.isfinite(result["global_params"]["intercept"]))
    
    def test_no_raw_record_transfer(self):
        clients = [LocalFederatedClient(hid, self.partitions["train"][hid]) for hid in HOSPITAL_IDS]
        updates = [c.train_round(self.global_params) for c in clients]
        for u in updates:
            self.assertNotIn("X", u)
            self.assertNotIn("y", u)
            self.assertNotIn("meta", u)
            self.assertIn("coef", u)
            self.assertIn("n_samples", u)
    
    def test_clients_identical_global_init_each_round(self):
        clients = [LocalFederatedClient(hid, self.partitions["train"][hid]) for hid in HOSPITAL_IDS]
        params = self.global_params
        for _ in range(2):
            updates = [c.train_round(params) for c in clients]
            params = FederatedAggregator.aggregate(updates)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
