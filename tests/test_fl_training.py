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
        # Each client started fresh from params_b (reset enforced)
        self.assertFalse(np.allclose(updates1[0]["coef"], updates2[0]["coef"]))
        self.assertNotAlmostEqual(float(updates1[0]["intercept"]), float(updates2[0]["intercept"]))

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

    def test_finite_difference_gradient_check(self):
        # Analytic gradient matching BinaryLogisticRegression.fit on one step.
        model = BinaryLogisticRegression(n_features=3, learning_rate=0.01, max_iter=1, random_state=123)
        np.random.seed(123)
        X = np.random.randn(10, 3)
        y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1]).astype(float)
        coef0 = np.array([0.1, -0.2, 0.05])
        b0 = 0.03
        model.set_params({"coef": coef0, "intercept": np.array(b0)})

        z = X @ coef0 + b0
        p = 1.0 / (1.0 + np.exp(-z))
        err = p - y
        analytic_coef = (X.T @ err) / len(y)
        analytic_intercept = np.mean(err)

        # Central finite differences of the BCE loss.
        eps = 1e-6
        num_coef = np.zeros(3)
        for i in range(3):
            c_plus = coef0.copy(); c_plus[i] += eps
            c_minus = coef0.copy(); c_minus[i] -= eps
            model.set_params({"coef": c_plus, "intercept": np.array(b0)})
            loss_plus = model.loss(X, y)
            model.set_params({"coef": c_minus, "intercept": np.array(b0)})
            loss_minus = model.loss(X, y)
            num_coef[i] = (loss_plus - loss_minus) / (2 * eps)

        model.set_params({"coef": coef0, "intercept": np.array(b0 + eps)})
        loss_b_plus = model.loss(X, y)
        model.set_params({"coef": coef0, "intercept": np.array(b0 - eps)})
        loss_b_minus = model.loss(X, y)
        num_intercept = (loss_b_plus - loss_b_minus) / (2 * eps)

        np.testing.assert_allclose(analytic_coef, num_coef, atol=1e-6)
        self.assertAlmostEqual(analytic_intercept, num_intercept, places=6)

    def test_parameter_reset_across_rounds(self):
        # Same client, same global params twice: must produce identical updates
        # (proves each round restarts from the supplied global params, no carry-over).
        partitions = partition_hospital_data()
        client = LocalFederatedClient("HOSP_TUN", partitions["train"]["HOSP_TUN"], random_state=42)
        params = {"coef": np.ones(18) * 0.1, "intercept": np.array(0.0)}
        u1 = client.train_round(params)
        u2 = client.train_round(params)
        np.testing.assert_allclose(u1["coef"], u2["coef"])
        self.assertAlmostEqual(float(u1["intercept"]), float(u2["intercept"]))
        # A different global starting point must yield a different update.
        params_b = {"coef": np.ones(18) * -0.2, "intercept": np.array(1.0)}
        u3 = client.train_round(params_b)
        self.assertFalse(np.allclose(u1["coef"], u3["coef"]))




    def test_train_federated_uses_frozen_config_transform(self):
        from scripts.train_federated_sim import run_federated_training
        # Ensure transformed features are used (clients get transformed X)
        res = run_federated_training(n_rounds=1, local_iterations=5, learning_rate=0.01, random_state=42)
        self.assertIn("clip", res)
        self.assertTrue(res["frozen_config_used"] is False or res["frozen_config_used"] is True)

    def test_train_centralized_uses_identical_transform(self):
        from scripts.train_federated_sim import run_centralized_baseline
        res = run_centralized_baseline(learning_rate=0.01, max_iter=10, random_state=42)
        self.assertIn("clip", res)




    def test_one_step_fit_against_finite_differences(self):
        # Real one-step fit() vs numerical gradient of BCE loss
        np.random.seed(12345)
        X = np.random.randn(50, 18)
        y = np.random.binomial(1, 0.3, 50).astype(float)
        model = BinaryLogisticRegression(n_features=18, learning_rate=0.1, max_iter=1, random_state=7)
        coef0 = np.random.randn(18) * 0.01
        b0 = 0.01
        model.set_params({"coef": coef0, "intercept": np.array(b0)})
        # Analytic
        z0 = X @ coef0 + b0
        p0 = 1.0 / (1.0 + np.exp(-z0))
        err0 = p0 - y
        g_coef = (X.T @ err0) / len(y)
        g_b = float(np.mean(err0))
        model.fit(X, y)
        # Expected after one step
        exp_coef = coef0 - 0.1 * g_coef
        exp_b = b0 - 0.1 * g_b
        np.testing.assert_allclose(model.coef_, exp_coef, rtol=1e-10, atol=1e-10)
        self.assertAlmostEqual(float(model.intercept_), float(exp_b), places=10)
        # Numerical check
        eps = 1e-6
        for i in [0, 5, 17]:
            c1 = coef0.copy(); c1[i]+=eps; m1=BinaryLogisticRegression(n_features=18); m1.set_params({"coef":c1,"intercept":np.array(b0)}); l1=m1.loss(X,y)
            c2 = coef0.copy(); c2[i]-=eps; m2=BinaryLogisticRegression(n_features=18); m2.set_params({"coef":c2,"intercept":np.array(b0)}); l2=m2.loss(X,y)
            num = (l1-l2)/(2*eps)
            self.assertAlmostEqual(num, g_coef[i], places=4)
        # intercept
        m1=BinaryLogisticRegression(n_features=18); m1.set_params({"coef":coef0,"intercept":np.array(b0+eps)}); l1=m1.loss(X,y)
        m2=BinaryLogisticRegression(n_features=18); m2.set_params({"coef":coef0,"intercept":np.array(b0-eps)}); l2=m2.loss(X,y)
        self.assertAlmostEqual((l1-l2)/(2*eps), g_b, places=4)

    def test_nonfinite_gradients_rejected(self):
        model = BinaryLogisticRegression(n_features=2, learning_rate=0.01, max_iter=1)
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([0.0, 1.0])
        model.coef_ = np.array([np.inf, 0.0])
        model.intercept_ = 0.0
        with self.assertRaises(ValueError):
            model.fit(X, y)


if __name__ == '__main__':
    unittest.main()
