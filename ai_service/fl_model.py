#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Small deterministic NumPy binary logistic-regression model compatible with later
parameter averaging (Federated Averaging).

This is a minimal implementation for MONITUS Step 3.4 micro-step 1:
- 18-dimensional feature input
- explicit weight vector and intercept
- numerically stable sigmoid and binary cross-entropy
- gradient-descent training with documented learning rate and iterations
- predict probabilities and binary classes with configurable threshold
- explicit get/set parameter methods using copies and shape checks
- validation for empty inputs, non-finite values, invalid labels, incompatible dimensions

Important notes:
- No formal privacy guarantee from FedAvg; this is a simulation only.
- Uses a fixed, explicitly documented transformation only if/when added later;
  for micro-step 1 this module only implements the model.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any

import numpy as np


class BinaryLogisticRegression:
    """
    Deterministic binary logistic regression implemented with NumPy.

    Parameters:
    - n_features: int = 18 (fixed for MONITUS ML features)
    - learning_rate: float = 0.01 (documented)
    - max_iter: int = 1000 (documented)
    - class_weight: Optional[str] = None (kept simple for now; can be 'balanced' if needed)
    - random_state: Optional[int] = 42 for deterministic initialization
    """

    def __init__(
        self,
        n_features: int = 18,
        learning_rate: float = 0.01,
        max_iter: int = 1000,
        class_weight: Optional[str] = None,
        random_state: Optional[int] = 42,
    ):
        if not isinstance(n_features, int) or n_features <= 0:
            raise ValueError("n_features must be a positive integer")
        if not np.isfinite(learning_rate) or learning_rate <= 0:
            raise ValueError("learning_rate must be a positive finite number")
        if not isinstance(max_iter, int) or max_iter <= 0:
            raise ValueError("max_iter must be a positive integer")
        if class_weight is not None and class_weight != "balanced":
            raise ValueError("class_weight must be None or 'balanced'")
        if random_state is not None and not isinstance(random_state, int):
            raise ValueError("random_state must be an int or None")

        self.n_features = int(n_features)
        self.learning_rate = float(learning_rate)
        self.max_iter = int(max_iter)
        self.class_weight = class_weight
        self.random_state = random_state

        # Initialize parameters
        rng = np.random.RandomState(self.random_state)
        self.coef_ = rng.normal(loc=0.0, scale=0.01, size=(self.n_features,))
        self.intercept_ = 0.0
        self.is_fitted_ = False

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid function."""
        # Clip to avoid overflow
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    @staticmethod
    def _binary_cross_entropy(y_true: np.ndarray, y_pred_proba: np.ndarray, eps: float = 1e-15) -> float:
        """Numerically stable binary cross-entropy."""
        y_pred_proba = np.clip(y_pred_proba, eps, 1.0 - eps)
        loss = -np.mean(y_true * np.log(y_pred_proba) + (1 - y_true) * np.log(1 - y_pred_proba))
        return float(loss)

    def _validate_X_y(self, X, y):
        """Validate inputs."""
        X = np.asarray(X)
        y = np.asarray(y)

        if X.size == 0:
            raise ValueError("X cannot be empty")
        if y.size == 0:
            raise ValueError("y cannot be empty")
        if X.ndim != 2:
            raise ValueError("X must be 2-dimensional (n_samples, n_features)")
        if y.ndim != 1:
            # Reject column vectors like (n,1)
            if y.ndim == 2 and y.shape[1] == 1:
                raise ValueError("y must be 1-dimensional (n_samples,), not column vector (n,1)")
            raise ValueError("y must be 1-dimensional (n_samples,)")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have the same number of samples")
        if X.shape[1] != self.n_features:
            raise ValueError(f"X must have {self.n_features} features, got {X.shape[1]}")
        if not np.all(np.isfinite(X)):
            raise ValueError("X contains non-finite values")
        if not np.all(np.isfinite(y)):
            raise ValueError("y contains non-finite values")
        # Check labels are 0 or 1
        unique_labels = np.unique(y)
        if not np.all(np.isin(unique_labels, [0, 1])):
            raise ValueError("y must contain only 0 and 1 labels")

        return X.astype(float), y.ravel().astype(float)

    def fit(self, X, y) -> "BinaryLogisticRegression":
        """
        Train using gradient descent starting from current model parameters.
        A federated client must use set_params(global_params) before every local round
        to begin optimization from the shared global model.
        """
        X, y = self._validate_X_y(X, y)
        n_samples = X.shape[0]

        # Compute class weights if needed
        if self.class_weight == "balanced":
            n_pos = np.sum(y)
            n_neg = n_samples - n_pos
            if n_pos == 0 or n_neg == 0:
                # Avoid division issues
                sample_weight = np.ones(n_samples)
            else:
                weight_pos = n_samples / (2.0 * n_pos)
                weight_neg = n_samples / (2.0 * n_neg)
                sample_weight = np.where(y == 1, weight_pos, weight_neg)
        else:
            sample_weight = np.ones(n_samples)

        # Gradient descent
        for _ in range(self.max_iter):
            # Forward pass
            z = X @ self.coef_ + self.intercept_
            y_pred = self._sigmoid(z)
            if not np.all(np.isfinite(y_pred)):
                raise ValueError("Non-finite probabilities produced")

            # Compute gradients
            error = y_pred - y
            if not np.all(np.isfinite(error)):
                raise ValueError("Non-finite gradients produced")
            # Apply sample weights
            weighted_error = error * sample_weight
            grad_coef = (X.T @ weighted_error) / n_samples
            grad_intercept = np.mean(weighted_error)
            if not np.all(np.isfinite(grad_coef)) or not np.isfinite(grad_intercept):
                raise ValueError("Non-finite gradients produced")

            # Update parameters
            self.coef_ = self.coef_ - self.learning_rate * grad_coef
            self.intercept_ = float(self.intercept_ - self.learning_rate * grad_intercept)
            if not np.all(np.isfinite(self.coef_)) or not np.isfinite(self.intercept_):
                raise ValueError("Non-finite parameter update produced")

        self.is_finite_ = True  # track finite state
        self.is_fitted_ = True
        return self

    def predict_proba(self, X) -> np.ndarray:
        """
        Predict class probabilities.
        Returns array of shape (n_samples,) with probability of class 1.
        """
        if not self.is_fitted_ and (np.allclose(self.coef_, 0) and self.intercept_ == 0):
            # Allow prediction even if not explicitly fitted (for testing)
            pass

        X = np.asarray(X)
        if X.size == 0:
            raise ValueError("X cannot be empty")
        if X.ndim == 1:
            if X.shape[0] != self.n_features:
                raise ValueError(f"X must have {self.n_features} features")
            X = X.reshape(1, -1)
        elif X.ndim == 2:
            if X.shape[1] != self.n_features:
                raise ValueError(f"X must have {self.n_features} features, got {X.shape[1]}")
        else:
            raise ValueError("X must be 1D or 2D array")

        if not np.all(np.isfinite(X)):
            raise ValueError("X contains non-finite values")

        z = X @ self.coef_ + self.intercept_
        proba = self._sigmoid(z)
        return proba

    def predict(self, X, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary classes with configurable threshold.
        """
        if not np.isfinite(threshold) or threshold < 0 or threshold > 1:
            raise ValueError("threshold must be between 0 and 1")
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def get_params(self) -> Dict[str, np.ndarray]:
        """
        Get parameters as copies for safe averaging.
        """
        return {
            "coef": self.coef_.copy(),
            "intercept": np.array(self.intercept_).copy(),
        }

    def set_params(self, params: Dict[str, Any]) -> "BinaryLogisticRegression":
        """
        Set parameters with copies and shape checks.
        """
        if not isinstance(params, dict):
            raise ValueError("params must be a dict")
        if "coef" not in params or "intercept" not in params:
            raise ValueError("params must contain 'coef' and 'intercept'")

        coef = np.asarray(params["coef"])
        intercept = np.asarray(params["intercept"])

        if coef.shape != (self.n_features,):
            raise ValueError(f"coef must have shape ({self.n_features},), got {coef.shape}")
        if intercept.shape != ():
            raise ValueError("intercept must be a scalar")
        if not np.all(np.isfinite(coef)):
            raise ValueError("coef contains non-finite values")
        if not np.all(np.isfinite(intercept)):
            raise ValueError("intercept contains non-finite values")

        self.coef_ = coef.copy()
        self.intercept_ = float(intercept)
        self.is_fitted_ = True
        return self

    def score(self, X, y) -> float:
        """Compute accuracy."""
        X, y = self._validate_X_y(X, y)
        predictions = self.predict(X)
        return float(np.mean(predictions == y))

    def loss(self, X, y) -> float:
        """Compute binary cross-entropy loss."""
        X, y = self._validate_X_y(X, y)
        proba = self.predict_proba(X)
        return self._binary_cross_entropy(y, proba)
