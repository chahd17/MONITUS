#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Federated training orchestration + centralized baseline for MONITUS Step 3.4 (micro-step 5).
Multi-round FedAvg with per-round global reset from identical parameters.

Public entry points route through the shared fixed preprocessing transform and
respect the frozen configuration when provided. Unused validation-selection
arguments are removed or ignored explicitly (no misleading behavior).
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression
from ai_service.fl_client import LocalFederatedClient
from ai_service.fl_server import FederatedAggregator
from ai_service.fl_utils import (
    partition_hospital_data,
    get_partition_summary,
    HOSPITAL_IDS,
    apply_fixed_feature_transform,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
FROZEN_CONFIG_PATH = REPORTS_DIR / "fl_frozen_config.json"


def _load_frozen_config(config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = config_path or FROZEN_CONFIG_PATH
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def run_federated_training(
    n_rounds: int = 5,
    local_iterations: int = 10,
    learning_rate: float = 0.01,
    random_state: int = 42,
    use_validation_for_selection: bool = False,
    config_path: Optional[Path] = ...,
    clip: Optional[float] = None,
    use_frozen_config: bool = True,
):
    """
    Run multi-round FedAvg. All clients initialize each round from identical global params.
    Hyperparameters must be selected on train/val only (not test). Use frozen
    configuration for consistent preprocessing between federated and centralized paths.
    """
    if config_path is ... and use_frozen_config:
        frozen = _load_frozen_config(None)
    elif config_path is None and use_frozen_config:
        frozen = _load_frozen_config(None)
    elif config_path not in (None, ...):
        frozen = _load_frozen_config(config_path)
    else:
        frozen = None
    # Only apply frozen config if caller didn't explicitly override key params
    if frozen is not None:
        if n_rounds == 5 and local_iterations == 10 and learning_rate == 0.01 and random_state == 42:
            n_rounds = int(frozen.get("rounds", n_rounds))
            local_iterations = int(frozen.get("local_iterations", local_iterations))
            learning_rate = float(frozen.get("learning_rate", learning_rate))
            random_state = int(frozen.get("random_state", random_state))
        if clip is None:
            clip = frozen.get("clip")

    np.random.seed(random_state)
    random.seed(random_state)

    partitions = partition_hospital_data()

    # Initialize global model
    global_model = BinaryLogisticRegression(
        n_features=18,
        learning_rate=learning_rate,
        max_iter=local_iterations,
        class_weight=None,  # unweighted
        random_state=random_state,
    )
    global_params = global_model.get_params()

    # Create clients (one per hospital) with transformed features
    clients = {}
    for hid in HOSPITAL_IDS:
        X_t = apply_fixed_feature_transform(partitions["train"][hid]["X"], clip)
        clients[hid] = LocalFederatedClient(
            hid,
            {
                "X": X_t,
                "y": partitions["train"][hid]["y"],
                "meta": partitions["train"][hid]["meta"],
            },
            learning_rate=learning_rate,
            local_iterations=local_iterations,
            random_state=random_state,
        )

    history = []
    for round_num in range(n_rounds):
        # Collect updates from all clients starting from identical global params
        updates = []
        for hid in HOSPITAL_IDS:
            update = clients[hid].train_round(global_params)
            updates.append(update)
        # Aggregate
        global_params = FederatedAggregator.aggregate(updates)
        history.append({"round": round_num, "n_clients": len(updates), "clip": clip})

    return {
        "global_params": global_params,
        "history": history,
        "partitions": partitions,
        "clip": clip,
        "frozen_config_used": frozen is not None,
    }


def run_centralized_baseline(
    learning_rate: float = 0.01,
    max_iter: int = 50,
    random_state: int = 42,
    config_path: Optional[Path] = None,
    clip: Optional[float] = None,
):
    """
    Centralized baseline using SAME NumPy logistic regression.
    Pools training data ONLY in this explicitly labeled offline benchmark path.
    Uses same features, same train split, identical preprocessing.
    """
    frozen = _load_frozen_config(config_path)
    if frozen is not None:
        learning_rate = float(frozen.get("learning_rate", learning_rate))
        random_state = int(frozen.get("random_state", random_state))
        if clip is None:
            clip = frozen.get("clip")
        if max_iter == 50:
            max_iter = int(frozen.get("rounds", 5)) * int(frozen.get("local_iterations", 10))

    np.random.seed(random_state)
    random.seed(random_state)

    partitions = partition_hospital_data()

    # Pool training data only (explicitly labeled offline benchmark) with identical transform
    X_train_list = []
    y_train_list = []
    for hid in HOSPITAL_IDS:
        X_train_list.append(apply_fixed_feature_transform(partitions["train"][hid]["X"], clip))
        y_train_list.append(partitions["train"][hid]["y"])
    X_train = np.vstack(X_train_list)
    y_train = np.concatenate(y_train_list)

    model = BinaryLogisticRegression(
        n_features=18,
        learning_rate=learning_rate,
        max_iter=max_iter,
        class_weight=None,
        random_state=random_state,
    )
    model.fit(X_train, y_train)

    return {
        "model": model,
        "params": model.get_params(),
        "n_train_samples": len(y_train),
        "clip": clip,
        "frozen_config_used": frozen is not None,
    }


def main():
    print("Running federated training...")
    fl_result = run_federated_training(n_rounds=3, local_iterations=5)
    print("Running centralized baseline...")
    central_result = run_centralized_baseline(max_iter=25)
    print("Done (orchestration only, no final test report)")


if __name__ == "__main__":
    main()
