#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused tests for BinaryLogisticRegression (Step 3.4 micro-step 1).
"""

import unittest

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression


class TestFLModel(unittest.TestCase):

    def test_initialization(self):
        model = BinaryLogisticRegression(n_features=18, learning_rate=0.01, max_iter=100, random_state=42)
        self.assertEqual(model.n_features, 18)
        self.assertEqual(model.learning_rate, 0.01)
        self.assertEqual(model.max_iter, 100)
        self.assertEqual(model.coef_.shape, (18,))
        self.assertIsInstance(model.intercept_, float)

    def test_sigmoid_numerical_stability(self):
        model = BinaryLogisticRegression()
        # Test extreme values
        z = np.array([-1000, -100, 0, 100, 1000])
        proba = model._sigmoid(z)
        self.assertTrue(np.all(np.isfinite(proba)))
        self.assertTrue(np.all(proba >= 0))
        self.assertTrue(np.all(proba <= 1))
        self.assertAlmostEqual(proba[2], 0.5)

    def test_predict_proba_shape_and_values(self):
        model = BinaryLogisticRegression(n_features=18, random_state=123)
        X = np.random.RandomState(456).randn(5, 18)
        proba = model.predict_proba(X)
        self.assertEqual(proba.shape, (5,))
        self.assertTrue(np.all(np.isfinite(proba)))
        self.assertTrue(np.all(proba >= 0))
        self.assertTrue(np.all(proba <= 1))

    def test_predict_proba_1d_input(self):
        model = BinaryLogisticRegression(n_features=18, random_state=123)
        X = np.random.RandomState(456).randn(18)
        proba = model.predict_proba(X)
        self.assertEqual(proba.shape, (1,))
        self.assertTrue(np.isfinite(proba[0]))

    def test_predict_with_threshold(self):
        model = BinaryLogisticRegression(n_features=18, random_state=123)
        X = np.random.RandomState(456).randn(10, 18)
        preds = model.predict(X, threshold=0.5)
        self.assertEqual(preds.shape, (10,))
        self.assertTrue(np.all(np.isin(preds, [0, 1])))

    def test_learning_reduces_loss(self):
        np.random.seed(42)
        X = np.random.randn(100, 18)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        model = BinaryLogisticRegression(n_features=18, learning_rate=0.1, max_iter=500, random_state=0)
        loss_before = model.loss(X, y)
        model.fit(X, y)
        loss_after = model.loss(X, y)
        self.assertLess(loss_after, loss_before)

    def test_deterministic_behavior(self):
        np.random.seed(999)
        X = np.random.randn(50, 18)
        y = np.random.randint(0, 2, 50)
        model1 = BinaryLogisticRegression(n_features=18, learning_rate=0.01, max_iter=100, random_state=42)
        model2 = BinaryLogisticRegression(n_features=18, learning_rate=0.01, max_iter=100, random_state=42)
        model1.fit(X, y)
        model2.fit(X, y)
        np.testing.assert_array_almost_equal(model1.coef_, model2.coef_)
        self.assertAlmostEqual(model1.intercept_, model2.intercept_)

    def test_get_set_params_with_copies(self):
        model = BinaryLogisticRegression(n_features=18, random_state=42)
        params = model.get_params()
        self.assertIn('coef', params)
        self.assertIn('intercept', params)
        self.assertEqual(params['coef'].shape, (18,))
        # Modify copy
        params['coef'][0] = 999
        # Original should be unchanged
        self.assertNotEqual(model.coef_[0], 999)
        # Set params
        new_params = {'coef': np.ones(18), 'intercept': np.array(0.5)}
        model.set_params(new_params)
        np.testing.assert_array_equal(model.coef_, np.ones(18))
        self.assertEqual(model.intercept_, 0.5)

    def test_shape_checks(self):
        model = BinaryLogisticRegression(n_features=18)
        with self.assertRaises(ValueError):
            model.set_params({'coef': np.ones(17), 'intercept': np.array(0.0)})
        with self.assertRaises(ValueError):
            model.set_params({'coef': np.ones(18), 'intercept': np.array([0.0, 1.0])})
        with self.assertRaises(ValueError):
            model.set_params({'coef': np.ones(18)})  # missing intercept

    def test_validation_empty_inputs(self):
        model = BinaryLogisticRegression(n_features=18)
        with self.assertRaises(ValueError):
            model.fit(np.array([]), np.array([]))
        with self.assertRaises(ValueError):
            model.predict_proba(np.array([]))

    def test_validation_non_finite(self):
        model = BinaryLogisticRegression(n_features=18)
        X = np.random.randn(10, 18)
        X[0, 0] = np.nan
        with self.assertRaises(ValueError):
            model.fit(X, np.ones(10))
        X = np.random.randn(10, 18)
        y = np.ones(10)
        y[0] = np.nan
        with self.assertRaises(ValueError):
            model.fit(X, y)
        X_bad = np.random.randn(10, 18)
        X_bad[0, 0] = np.inf
        with self.assertRaises(ValueError):
            model.predict_proba(X_bad)

    def test_validation_invalid_labels(self):
        model = BinaryLogisticRegression(n_features=18)
        X = np.random.randn(10, 18)
        y = np.array([0, 1, 2, 0, 1, 0, 1, 0, 1, 0])
        with self.assertRaises(ValueError):
            model.fit(X, y)

    def test_validation_incompatible_dimensions(self):
        model = BinaryLogisticRegression(n_features=18)
        X = np.random.randn(10, 17)
        y = np.random.randint(0, 2, 10)
        with self.assertRaises(ValueError):
            model.fit(X, y)
        X = np.random.randn(10, 19)
        with self.assertRaises(ValueError):
            model.fit(X, y)

    def test_binary_cross_entropy_stability(self):
        model = BinaryLogisticRegression()
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0.0, 1.0, 0.0, 1.0])
        loss = model._binary_cross_entropy(y_true, y_pred)
        self.assertTrue(np.isfinite(loss))
        self.assertLess(loss, 1e-10)

    def test_numerical_stability_extreme_features(self):
        model = BinaryLogisticRegression(n_features=18, learning_rate=0.01, max_iter=10, random_state=42)
        X = np.random.RandomState(123).randn(50, 18) * 1000
        y = np.random.RandomState(124).randint(0, 2, 50)
        model.fit(X, y)
        proba = model.predict_proba(X)
        self.assertTrue(np.all(np.isfinite(proba)))
        self.assertTrue(np.all(proba >= 0) and np.all(proba <= 1))

    def test_reject_column_vector_labels(self):
        # Regression: labels shaped (n, 1) must be rejected, not broadcast.
        model = BinaryLogisticRegression(n_features=3, random_state=0)
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        y = np.array([[0], [1], [0]])  # shape (n,1)
        with self.assertRaises(ValueError):
            model.fit(X, y)
        # Valid 1-D labels of the same values are accepted.
        model.fit(X, y.ravel())
        self.assertEqual(model.coef_.shape, (3,))

    def test_reject_1d_X(self):
        model = BinaryLogisticRegression(n_features=3, random_state=0)
        X = np.array([1.0, 2.0, 3.0])  # 1-D, not (n, 3)
        y = np.array([0, 1, 0])
        with self.assertRaises(ValueError):
            model.fit(X, y)

    def test_reject_shape_mismatches(self):
        model = BinaryLogisticRegression(n_features=3, random_state=0)
        X = np.array([[1, 2, 3], [4, 5, 6]])
        y = np.array([0, 1, 0])  # wrong length
        with self.assertRaises(ValueError):
            model.fit(X, y)


if __name__ == '__main__':
    unittest.main()
