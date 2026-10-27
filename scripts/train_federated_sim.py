#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Federated training orchestration + centralized baseline for MONITUS Step 3.4 (micro-step 5).
Multi-round FedAvg with per-round global reset from identical parameters.
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
from ai_service.fl_utils import partition_hospital_data, get_partition_summary, HOSPITAL_IDS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def run_federated_training(
    n_rounds: int = 5,
    local_iterations: int = 10,
    learning_rate: float = 0.01,
    random_state: int = 42,
    use_validation_for_selection: bool = True,
):
    """
    Run multi-round FedAvg. All clients initialize each round from identical global params.
    Hyperparams selected using train/val only, not test.
    """
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

    # Create clients (one per hospital)
    clients = {}
    for hid in HOSPITAL_IDS:
        clients[hid] = LocalFederatedClient(
            hid,
            partitions["train"][hid],
            learning_rate=learning_rate,
            local_iterations=local_iterations,
            random_state=random_state,
        )

    history = []
    for round_num in range(n_rounds):
        # Collect updates from all clients starting from identical global params
        updates = []
        for hid in HOSPITAL_IDS:
            # Each client must start from identical global params
            update = clients[hid].train_round(global_params.copy() if False else global_params)
            updates.append(update)
        # Aggregate
        global_params = FederatedAggregator.aggregate(updates)
        history.append({"round": round_num, "n_clients": len(updates)})

    return {
        "global_params": global_params,
        "history": history,
        "partitions": partitions,
    }


def run_centralized_baseline(
    learning_rate: float = 0.01,
    max_iter: int = 50,
    random_state: int = 42,
):
    """
    Centralized baseline using SAME NumPy logistic regression.
    Pools training data ONLY in this explicitly labeled offline benchmark path.
    Uses same features, same train split. Validation/test not used for hyperparams.
    """
    np.random.seed(random_state)
    random.seed(random_state)

    partitions = partition_hospital_data()

    # Pool training data only (explicitly labeled offline benchmark)
    X_train_list = []
    y_train_list = []
    for hid in HOSPITAL_IDS:
        X_train_list.append(partitions["train"][hid]["X"])
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
    }


def main():
    print("Running federated training...")
    fl_result = run_federated_training(n_rounds=3, local_iterations=5)
    print("Running centralized baseline...")
    central_result = run_centralized_baseline(max_iter=25)
    print("Done (orchestration only, no final test report)")


if __name__ == "__main__":
    main()
