#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedAvg aggregation server for MONITUS Step 3.4 (micro-step 4).
Deterministic weighted averaging of local model updates only.

Notes:
- Only accepts updates with hospital_id, coef, intercept, n_samples
- Weights = n_k / sum(n_k) (unequal sample counts allowed)
- Never accepts raw data or metadata
- Returns copied arrays; never mutates client updates
- No formal privacy guarantee; model updates can leak information
"""

from __future__ import annotations

from typing import Dict, List, Any
import numpy as np


class FederatedAggregator:
    """Deterministic FedAvg aggregator."""

    @staticmethod
    def aggregate(updates: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """
        Aggregate updates using weighted FedAvg.
        Returns dict with coef and intercept as copies.
        """
        if not isinstance(updates, (list, tuple)):
            raise ValueError("updates must be a list")
        if len(updates) == 0:
            raise ValueError("Cannot aggregate empty update collection")

        # Check for raw data and enforce exact schema
        forbidden = ["x", "y", "meta", "features", "history", "raw", "provenance", "patient_records"]
        allowed = {"hospital_id", "coef", "intercept", "n_samples"}
        for update in updates:
            if not isinstance(update, dict):
                raise ValueError("Each update must be a dict")
            for key in update.keys():
                if key.lower() in forbidden or key in ["X", "Y", "META"]:
                    raise ValueError("Raw data not allowed in updates")
                if key not in allowed:
                    raise ValueError(f"Unexpected field in update: {key}")
            required = ["hospital_id", "coef", "intercept", "n_samples"]
            for req in required:
                if req not in update:
                    raise ValueError(f"Missing required field: {req}")
            if set(update.keys()) != allowed:
                raise ValueError("Update must contain only hospital_id, coef, intercept, n_samples")

        # Check duplicates
        hospital_ids = [u["hospital_id"] for u in updates]
        if len(hospital_ids) != len(set(hospital_ids)):
            raise ValueError("Duplicate hospital IDs not allowed")

        # Validate and collect
        validated = []
        for update in updates:
            hid = update["hospital_id"]
            if not isinstance(hid, str) or not hid.strip():
                raise ValueError("hospital_id must be non-empty string")
            coef = np.asarray(update["coef"]).copy()
            intercept = np.asarray(update["intercept"]).copy()
            n_samples = update["n_samples"]

            if not isinstance(n_samples, (int, np.integer)):
                raise ValueError("n_samples must be integer")
            if n_samples <= 0:
                raise ValueError("n_samples must be positive")
            if not np.all(np.isfinite(coef)):
                raise ValueError("Non-finite coefficients")
            if not np.all(np.isfinite(intercept)):
                raise ValueError("Non-finite intercept")
            if coef.ndim != 1:
                raise ValueError("coef must be 1-dimensional")
            if intercept.shape != ():
                raise ValueError("intercept must be scalar")

            validated.append({
                "hospital_id": hid,
                "coef": coef,
                "intercept": float(intercept),
                "n_samples": int(n_samples),
            })

        # Check dimensions
        n_features = validated[0]["coef"].shape[0]
        for v in validated:
            if v["coef"].shape[0] != n_features:
                raise ValueError("Incompatible coefficient dimensions")

        # Compute weighted average
        total_samples = sum(v["n_samples"] for v in validated)
        if total_samples == 0:
            raise ValueError("Total samples cannot be zero")

        aggregated_coef = np.zeros(n_features)
        aggregated_intercept = 0.0

        for v in validated:
            weight = v["n_samples"] / total_samples
            aggregated_coef += weight * v["coef"]
            aggregated_intercept += weight * v["intercept"]

        if not np.all(np.isfinite(aggregated_coef)) or not np.isfinite(aggregated_intercept):
            raise ValueError("Non-finite aggregation result")

        return {
            "coef": aggregated_coef.copy(),
            "intercept": np.array(aggregated_intercept).copy(),
        }
