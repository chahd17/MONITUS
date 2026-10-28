#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused tests for FedAvg aggregation server (Step 3.4 micro-step 4).
"""

import unittest

import numpy as np

from ai_service.fl_server import FederatedAggregator


class TestFLServer(unittest.TestCase):

    def test_weighted_averaging_basic(self):
        updates = [
            {"hospital_id": "H1", "coef": np.array([1.0, 2.0, 3.0]), "intercept": np.array(0.5), "n_samples": 10},
            {"hospital_id": "H2", "coef": np.array([3.0, 4.0, 5.0]), "intercept": np.array(1.5), "n_samples": 10},
        ]
        result = FederatedAggregator.aggregate(updates)
        np.testing.assert_array_almost_equal(result["coef"], np.array([2.0, 3.0, 4.0]))
        self.assertAlmostEqual(float(result["intercept"]), 1.0)

    def test_unequal_sample_counts(self):
        updates = [
            {"hospital_id": "TUN", "coef": np.array([1.0, 0.0]), "intercept": np.array(0.0), "n_samples": 100},
            {"hospital_id": "SOU", "coef": np.array([3.0, 0.0]), "intercept": np.array(0.0), "n_samples": 200},
        ]
        result = FederatedAggregator.aggregate(updates)
        # weighted: (100*1 + 200*3)/(300) = (100 + 600)/300 = 700/300 = 2.333...
        np.testing.assert_array_almost_equal(result["coef"][0], 7.0/3.0)

    def test_intercept_aggregation(self):
        updates = [
            {"hospital_id": "A", "coef": np.zeros(5), "intercept": np.array(1.0), "n_samples": 1},
            {"hospital_id": "B", "coef": np.zeros(5), "intercept": np.array(3.0), "n_samples": 3},
        ]
        result = FederatedAggregator.aggregate(updates)
        self.assertAlmostEqual(float(result["intercept"]), (1*1 + 3*3)/4)

    def test_update_order_independence(self):
        u1 = {"hospital_id": "A", "coef": np.array([1.0, 2.0]), "intercept": np.array(0.5), "n_samples": 10}
        u2 = {"hospital_id": "B", "coef": np.array([3.0, 4.0]), "intercept": np.array(1.5), "n_samples": 20}
        r1 = FederatedAggregator.aggregate([u1, u2])
        r2 = FederatedAggregator.aggregate([u2, u1])
        np.testing.assert_array_almost_equal(r1["coef"], r2["coef"])
        self.assertAlmostEqual(float(r1["intercept"]), float(r2["intercept"]))

    def test_duplicate_hospital_ids_rejected(self):
        updates = [
            {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 10},
            {"hospital_id": "A", "coef": np.array([2.0]), "intercept": np.array(0.0), "n_samples": 10},
        ]
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate(updates)

    def test_empty_updates_rejected(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([])

    def test_invalid_sample_counts(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": -1}
            ])
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 0}
            ])
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 0},
                {"hospital_id": "B", "coef": np.array([2.0]), "intercept": np.array(0.0), "n_samples": 0},
            ])

    def test_nan_inf_rejected(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([np.nan]), "intercept": np.array(0.0), "n_samples": 10}
            ])
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(np.inf), "n_samples": 10}
            ])

    def test_incompatible_dimensions(self):
        updates = [
            {"hospital_id": "A", "coef": np.array([1.0, 2.0]), "intercept": np.array(0.0), "n_samples": 10},
            {"hospital_id": "B", "coef": np.array([1.0, 2.0, 3.0]), "intercept": np.array(0.0), "n_samples": 10},
        ]
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate(updates)

    def test_raw_data_rejected(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 10, "X": [[1,2]]}
            ])

    def test_no_mutation_of_updates(self):
        coef1 = np.array([1.0, 2.0])
        updates = [
            {"hospital_id": "A", "coef": coef1, "intercept": np.array(0.5), "n_samples": 10},
            {"hospital_id": "B", "coef": np.array([3.0, 4.0]), "intercept": np.array(1.5), "n_samples": 20},
        ]
        result = FederatedAggregator.aggregate(updates)
        result["coef"][0] = 999
        np.testing.assert_array_equal(coef1, np.array([1.0, 2.0]))

    def test_determinism(self):
        updates = [
            {"hospital_id": "A", "coef": np.array([1.5, 2.5]), "intercept": np.array(0.3), "n_samples": 15},
            {"hospital_id": "B", "coef": np.array([2.5, 3.5]), "intercept": np.array(0.7), "n_samples": 25},
        ]
        r1 = FederatedAggregator.aggregate(updates)
        r2 = FederatedAggregator.aggregate(updates)
        np.testing.assert_array_equal(r1["coef"], r2["coef"])
        self.assertEqual(float(r1["intercept"]), float(r2["intercept"]))

    def test_manual_weighted_average_three_hospitals(self):
        # Unequal counts
        updates = [
            {"hospital_id": "TUN", "coef": np.array([1.0, 0.5]), "intercept": np.array(0.0), "n_samples": 560},
            {"hospital_id": "SOU", "coef": np.array([2.0, 1.5]), "intercept": np.array(1.0), "n_samples": 560},
            {"hospital_id": "SFX", "coef": np.array([0.5, 0.2]), "intercept": np.array(-0.5), "n_samples": 560},
        ]
        total = 1680
        result = FederatedAggregator.aggregate(updates)
        expected_coef = (560*1.0 + 560*2.0 + 560*0.5)/total, (560*0.5 + 560*1.5 + 560*0.2)/total
        expected_intercept = (560*0.0 + 560*1.0 + 560*(-0.5))/total
        np.testing.assert_array_almost_equal(result["coef"], np.array(expected_coef))
        self.assertAlmostEqual(float(result["intercept"]), expected_intercept)

    def test_reject_unknown_keys_including_patient_records(self):
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 10, "patient_records": []}
            ])
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "intercept": np.array(0.0), "n_samples": 10, "extra": 123}
            ])

    def test_exact_schema_only(self):
        # Missing required field
        with self.assertRaises(ValueError):
            FederatedAggregator.aggregate([
                {"hospital_id": "A", "coef": np.array([1.0]), "n_samples": 10}
            ])


if __name__ == '__main__':
    unittest.main()
