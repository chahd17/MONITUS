#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local federated client for MONITUS Step 3.4 (micro-step 3).
Owns exactly one hospital's local training partition. No aggregation.

Notes:
- This is only a federated simulation; no formal privacy guarantee.
- Each round: client receives global coefficients/intercept, calls set_params() BEFORE fit().
- Trains only on its own partition. Returns only parameters + counts + hospital id.
- Never returns raw X, y, metadata, feature histories.
- No class_weight='balanced' by default (Sfax has 0 positives).
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import copy

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression


class LocalFederatedClient:
    """Federated client bound to a single hospital partition."""

    def __init__(
        self,
        hospital_id: str,
        partition: Dict[str, Any],
        n_features: int = 18,
        learning_rate: float = 0.01,
        local_iterations: int = 100,
        random_state: Optional[int] = None,
    ):
        if not isinstance(hospital_id, str) or not hospital_id.strip():
            raise ValueError("hospital_id must be a non-empty string")
        if not isinstance(partition, dict):
            raise ValueError("partition must be a dict")
        required_keys = {"X", "y", "meta"}
        if not all(k in partition for k in required_keys):
            raise ValueError("partition must contain X, y, meta")

        self.hospital_id = hospital_id
        self.partition = partition
        self.n_features = int(n_features)
        self.learning_rate = float(learning_rate)
        self.local_iterations = int(local_iterations)
        self.random_state = random_state

        # Validate partition
        X = np.asarray(partition["X"])
        y = np.asarray(partition["y"])
        meta = partition.get("meta")

        # Enforce shape: X must be (n, n_features), y must be 1D (n,)
        if X.ndim != 2:
            raise ValueError("X must be 2-dimensional (n_samples, n_features)")
        if y.ndim != 1:
            raise ValueError("y must be 1-dimensional (n_samples,)")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have same number of samples")
        if X.shape[0] == 0:
            # Consistent with the server, which rejects n_samples <= 0 updates.
            raise ValueError("Client partition must contain at least one training sample")
        if X.shape[1] != self.n_features:
            raise ValueError(f"Partition must have {self.n_features} features")
        if not np.all(np.isfinite(X)):
            raise ValueError("Partition contains non-finite features")
        if not np.all(np.isfinite(y)):
            raise ValueError("Partition contains non-finite labels")
        unique_labels = np.unique(y)
        if not np.all(np.isin(unique_labels, [0, 1])):
            raise ValueError("Labels must be 0 or 1")

        # Enforce hospital_id consistency with metadata
        if meta is None:
            raise ValueError("Metadata must be provided")
        if not isinstance(meta, (list, tuple)):
            raise ValueError("Metadata must be a list")
        if len(meta) != int(X.shape[0]):
            raise ValueError("Metadata must have exactly len(X) entries")
        for m in meta:
            if not isinstance(m, dict):
                raise ValueError("Metadata entries must be dicts")
            if "hospital_id" not in m or m.get("hospital_id") != self.hospital_id:
                raise ValueError("Metadata hospital_id mismatch")
            if "split" not in m or m.get("split") != "train":
                raise ValueError("Client only accepts train partition records")

        self.X_local = X.astype(float).copy()  # own copy
        self.y_local = y.astype(float).ravel().copy()
        self.n_samples = int(X.shape[0])

        # Model owned by client (separate from others)
        self.model = BinaryLogisticRegression(
            n_features=self.n_features,
            learning_rate=self.learning_rate,
            max_iter=self.local_iterations,
            class_weight=None,  # Do not use balanced - Sfax has 0 positives
            random_state=self.random_state,
        )

    def train_round(self, global_params: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Train one local round starting from global parameters.
        Must call set_params() with global_params BEFORE fit().
        Returns update with copied parameters only (no raw data).
        """
        if not isinstance(global_params, dict):
            raise ValueError("global_params must be a dict")
        if "coef" not in global_params or "intercept" not in global_params:
            raise ValueError("global_params must contain coef and intercept")

        # Load global parameters
        self.model.set_params(global_params)

        # Train only on own data
        if self.n_samples > 0:
            self.model.fit(self.X_local, self.y_local)
        # If all negative (e.g., Sfax), training is still finite with class_weight=None

        # Get parameters as copies
        params = self.model.get_params()
        coef = np.asarray(params["coef"])
        intercept = np.asarray(params["intercept"])

        if not np.all(np.isfinite(coef)) or not np.all(np.isfinite(intercept)):
            raise ValueError("Non-finite parameters produced")
        if coef.shape != (self.n_features,):
            raise ValueError("Invalid coefficient shape")
        if intercept.shape != ():
            raise ValueError("Invalid intercept shape")

        return {
            "hospital_id": self.hospital_id,
            "coef": coef.copy(),
            "intercept": intercept.copy(),
            "n_samples": int(self.n_samples),
        }

    def get_num_samples(self) -> int:
        return self.n_samples
