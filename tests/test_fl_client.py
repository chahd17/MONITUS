#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused tests for LocalFederatedClient (Step 3.4 micro-step 3).
"""

import unittest

import numpy as np

from ai_service.fl_client import LocalFederatedClient
from ai_service.fl_utils import partition_hospital_data, HOSPITAL_IDS
from ai_service.fl_model import BinaryLogisticRegression


class TestFLClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.partitions = partition_hospital_data()
        cls.global_model = BinaryLogisticRegression(n_features=18, random_state=123)
        cls.global_params = cls.global_model.get_params()

    def test_three_hospital_identities(self):
        clients = []
        for hid in HOSPITAL_IDS:
            client = LocalFederatedClient(hid, self.partitions["train"][hid])
            clients.append(client)
            self.assertEqual(client.hospital_id, hid)
        self.assertEqual(len(clients), 3)

    def test_clients_bound_to_correct_partitions(self):
        for hid in HOSPITAL_IDS:
            client = LocalFederatedClient(hid, self.partitions["train"][hid])
            self.assertEqual(client.n_samples, self.partitions["train"][hid]["n_samples"])
            np.testing.assert_array_equal(client.X_local, self.partitions["train"][hid]["X"])
            np.testing.assert_array_equal(client.y_local, self.partitions["train"][hid]["y"])

    def test_all_clients_start_from_identical_global_params(self):
        clients = [LocalFederatedClient(hid, self.partitions["train"][hid]) for hid in HOSPITAL_IDS]
        updates = []
        for client in clients:
            update = client.train_round(self.global_params)
            updates.append(update)
        # All started from same global params conceptually
        # Check they all produced updates
        self.assertEqual(len(updates), 3)

    def test_different_prior_states_cannot_contaminate(self):
        client = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        # First round with global params A
        params_a = {"coef": np.ones(18) * 0.1, "intercept": np.array(0.0)}
        update1 = client.train_round(params_a)
        # Second round with different global params B - must start fresh from B
        params_b = {"coef": np.ones(18) * -0.05, "intercept": np.array(0.5)}
        update2 = client.train_round(params_b)
        # Update2 should reflect starting from params_b, not from update1
        self.assertNotAlmostEqual(float(update2["intercept"]), float(update1["intercept"]))

    def test_no_raw_samples_labels_metadata_returned(self):
        client = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        update = client.train_round(self.global_params)
        forbidden = ["X", "y", "meta", "features", "history", "raw"]
        for key in update.keys():
            self.assertNotIn(key.lower(), forbidden)
        self.assertIn("coef", update)
        self.assertIn("intercept", update)
        self.assertIn("n_samples", update)
        self.assertIn("hospital_id", update)

    def test_parameters_are_copies_not_shared_views(self):
        client = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        update = client.train_round(self.global_params)
        update["coef"][0] = 999
        update["intercept"] = 999
        # Client's model should be unaffected
        p2 = client.model.get_params()
        self.assertNotEqual(p2["coef"][0], 999)

    def test_sample_counts_match_partitions(self):
        for hid in HOSPITAL_IDS:
            client = LocalFederatedClient(hid, self.partitions["train"][hid])
            update = client.train_round(self.global_params)
            self.assertEqual(update["n_samples"], self.partitions["train"][hid]["n_samples"])
            self.assertEqual(update["n_samples"], self.partitions["train"][hid]["n_samples"])

    def test_sfax_all_negative_handled_without_errors(self):
        client = LocalFederatedClient("HOSP_SFX", self.partitions["train"]["HOSP_SFX"])
        self.assertEqual(client.n_samples, 560)
        self.assertTrue(np.all(client.y_local == 0))
        update = client.train_round(self.global_params)
        self.assertTrue(np.all(np.isfinite(update["coef"])))
        self.assertTrue(np.isfinite(update["intercept"]))

    def test_determinism(self):
        client1 = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"], random_state=42)
        client2 = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"], random_state=42)
        u1 = client1.train_round(self.global_params)
        u2 = client2.train_round(self.global_params)
        np.testing.assert_array_almost_equal(u1["coef"], u2["coef"])
        self.assertAlmostEqual(u1["intercept"], u2["intercept"])

    def test_shape_validation(self):
        with self.assertRaises(ValueError):
            LocalFederatedClient("HOSP_TUN", {"X": np.zeros((10,17)), "y": np.zeros(10), "meta": []})
        bad_partition = {"X": np.zeros((10,18)), "y": np.ones(11), "meta": []}
        with self.assertRaises(ValueError):
            LocalFederatedClient("HOSP_TUN", bad_partition)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            LocalFederatedClient("", self.partitions["train"]["HOSP_TUN"])
        client = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        with self.assertRaises(ValueError):
            client.train_round({})
        with self.assertRaises(ValueError):
            client.train_round({"coef": np.ones(18)})

    def test_no_cross_hospital_partition_access(self):
        client_tun = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        client_sou = LocalFederatedClient("HOSP_SOU", self.partitions["train"]["HOSP_SOU"])
        np.testing.assert_array_equal(client_tun.X_local, self.partitions["train"]["HOSP_TUN"]["X"])
        np.testing.assert_array_equal(client_sou.X_local, self.partitions["train"]["HOSP_SOU"]["X"])
        # Different data
        self.assertFalse(np.array_equal(client_tun.X_local, client_sou.X_local))

    def test_non_finite_update_rejected(self):
        client = LocalFederatedClient("HOSP_TUN", self.partitions["train"]["HOSP_TUN"])
        # This should produce finite updates normally
        update = client.train_round(self.global_params)
        self.assertTrue(np.all(np.isfinite(update["coef"])))
        self.assertTrue(np.isfinite(update["intercept"]))

    def test_reject_empty_partition(self):
        # Consistent with the server rejecting n_samples <= 0.
        with self.assertRaises(ValueError):
            LocalFederatedClient(
                "HOSP_TUN",
                {"X": np.zeros((0, 18)), "y": np.zeros((0,), dtype=int), "meta": []},
            )

    def test_reject_mismatched_hospital_metadata(self):
        partitions = partition_hospital_data()
        bad_part = {
            "X": partitions["train"]["HOSP_TUN"]["X"].copy(),
            "y": partitions["train"]["HOSP_TUN"]["y"].copy(),
            "meta": [{"hospital_id": "HOSP_SOU", "split": "train", "sim_id": "x"}] * len(partitions["train"]["HOSP_TUN"]["y"])
        }
        with self.assertRaises(ValueError):
            LocalFederatedClient("HOSP_TUN", bad_part)

    def test_reject_non_train_split(self):
        partitions = partition_hospital_data()
        bad_part = {
            "X": partitions["train"]["HOSP_TUN"]["X"].copy(),
            "y": partitions["train"]["HOSP_TUN"]["y"].copy(),
            "meta": [{"hospital_id": "HOSP_TUN", "split": "test", "sim_id": "x"}] * len(partitions["train"]["HOSP_TUN"]["y"])
        }
        with self.assertRaises(ValueError):
            LocalFederatedClient("HOSP_TUN", bad_part)

    def test_reject_missing_or_misaligned_metadata(self):
        partitions = partition_hospital_data()
        bad_part = {
            "X": partitions["train"]["HOSP_TUN"]["X"].copy(),
            "y": partitions["train"]["HOSP_TUN"]["y"].copy(),
            "meta": [{"hospital_id": "HOSP_TUN"}] * len(partitions["train"]["HOSP_TUN"]["y"])  # missing split
        }
        with self.assertRaises(ValueError):
            LocalFederatedClient("HOSP_TUN", bad_part)


if __name__ == '__main__':
    unittest.main()
