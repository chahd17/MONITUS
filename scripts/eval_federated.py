#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical first evaluation for Step 3.4 - Federated vs Centralized on the v1
held-out test split (seeds 3001-3006).

IMPORTANT (post-review correction): the hyperparameters below were FIXED
DEFAULTS chosen by the developer, not the result of a documented search.
They were not selected with a recorded train/validation procedure. The earlier
claim of validation-based selection was inaccurate. A genuine train/validation
selection now lives in scripts/diagnose_federated_trainval.py and the fresh-seed
held-out evaluation in scripts/eval_federated_v2.py.

The v1 report (reports/fl_simulation.json) is preserved unchanged as history
and must not be re-tuned or overwritten.
"""

import json
import platform
from pathlib import Path
from datetime import datetime
import random

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression
from ai_service.fl_client import LocalFederatedClient
from ai_service.fl_server import FederatedAggregator
from ai_service.fl_utils import partition_hospital_data, HOSPITAL_IDS
from scripts.train_ml_detector import get_simulation_configs


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_model(model, X, y, threshold=0.5):
    if len(y) == 0:
        return {
            "tp": 0, "tn": 0, "fp": 0, "fn": 0,
            "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "accuracy": 0.0, "n_samples": 0
        }
    proba = model.predict_proba(X)
    pred = (proba >= threshold).astype(int)
    tp = int(np.sum((pred == 1) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y)
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": float(precision), "recall": float(recall), "f1": float(f1),
        "accuracy": float(accuracy), "n_samples": int(len(y))
    }


def main():
    random.seed(42)
    np.random.seed(42)

    partitions = partition_hospital_data()
    configs = get_simulation_configs()

    # FIXED DEFAULTS chosen by the developer (NOT selected via a documented
    # train/validation search). The historical v1 report must be read with this
    # caveat; see scripts/diagnose_federated_trainval.py for the real selection.
    n_rounds = 10
    local_iterations = 20
    learning_rate = 0.01
    threshold = 0.5  # fixed default, not tuned
    random_state = 42

    # Initialize global model
    global_model = BinaryLogisticRegression(
        n_features=18, learning_rate=learning_rate, max_iter=local_iterations,
        class_weight=None, random_state=random_state
    )
    global_params = global_model.get_params()

    # Create clients
    clients = {hid: LocalFederatedClient(hid, partitions["train"][hid],
                                          learning_rate=learning_rate,
                                          local_iterations=local_iterations,
                                          random_state=random_state)
               for hid in HOSPITAL_IDS}

    # Multi-round training
    convergence_history = []
    for round_num in range(n_rounds):
        updates = []
        for hid in HOSPITAL_IDS:
            # Each client starts from identical global params
            update = clients[hid].train_round(global_params)
            updates.append(update)
        global_params = FederatedAggregator.aggregate(updates)
        # Simple convergence metric
        convergence_history.append({"round": round_num})

    # Create global federated model
    fl_model = BinaryLogisticRegression(n_features=18, random_state=random_state)
    fl_model.set_params(global_params)

    # Centralized baseline - pool training data only
    X_train_central = np.vstack([partitions["train"][hid]["X"] for hid in HOSPITAL_IDS])
    y_train_central = np.concatenate([partitions["train"][hid]["y"] for hid in HOSPITAL_IDS])
    central_model = BinaryLogisticRegression(n_features=18, learning_rate=learning_rate,
                                             max_iter=100, class_weight=None,
                                             random_state=random_state)
    central_model.fit(X_train_central, y_train_central)

    # Evaluate on HELD-OUT TEST once
    results = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "branch": "feature/federated-simulation",
            "random_state": random_state,
            "n_rounds": n_rounds,
            "local_iterations": local_iterations,
            "learning_rate": learning_rate,
            "threshold": threshold,
            "class_weight": None,
            "normalization": "none (no transformation applied)",
            "feature_count": 18,
            "window_size": 21,
            "hyperparams_selected_on": "FIXED DEFAULTS (not a documented train/validation search)",
            "test_evaluated_once": True,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "privacy_warning": "ORDINARY FEDAVG HAS NO FORMAL PRIVACY GUARANTEE, NO SECURE AGGREGATION, AND NO DIFFERENTIAL PRIVACY. Model updates can leak information about local data. This is a simulation only.",
        "partitions": {
            "train": {hid: {"n_samples": int(partitions["train"][hid]["n_samples"]),
                           "n_pos": int(np.sum(partitions["train"][hid]["y"])),
                           "n_neg": int(len(partitions["train"][hid]["y"]) - np.sum(partitions["train"][hid]["y"])),
                           "sim_ids": sorted(list(set(m["sim_id"] for m in partitions["train"][hid]["meta"])))}
                     for hid in HOSPITAL_IDS},
            "val": {hid: {"n_samples": int(partitions["val"][hid]["n_samples"]),
                         "n_pos": int(np.sum(partitions["val"][hid]["y"])),
                         "n_neg": int(len(partitions["val"][hid]["y"]) - np.sum(partitions["val"][hid]["y"])),
                         "sim_ids": sorted(list(set(m["sim_id"] for m in partitions["val"][hid]["meta"])))}
                   for hid in HOSPITAL_IDS},
            "test": {hid: {"n_samples": int(partitions["test"][hid]["n_samples"]),
                          "n_pos": int(np.sum(partitions["test"][hid]["y"])),
                          "n_neg": int(len(partitions["test"][hid]["y"]) - np.sum(partitions["test"][hid]["y"])),
                          "sim_ids": sorted(list(set(m["sim_id"] for m in partitions["test"][hid]["meta"])))}
                    for hid in HOSPITAL_IDS},
        },
        "simulation_configs": configs,
        "federated": {"global": {}, "per_hospital": {}},
        "centralized": {"global": {}, "per_hospital": {}},
        "reporting_error_analysis": {},
        "convergence_history": convergence_history,
        "limitations": [
            "Simulation only - synthetic data from simplified generator",
            "No formal privacy guarantee (FedAvg only)",
            "Unweighted BCE with no class balancing; Sfax has all-negative training data",
            "No feature normalization applied (fixed transformation not implemented)",
            "Small number of simulations",
            "Windows are correlated (overlapping)",
            "Model not connected to API/dashboard",
            "Does not claim clinical outbreak detection"
        ]
    }

    # Global evaluation
    X_test_all = np.vstack([partitions["test"][hid]["X"] for hid in HOSPITAL_IDS])
    y_test_all = np.concatenate([partitions["test"][hid]["y"] for hid in HOSPITAL_IDS])
    results["federated"]["global"] = evaluate_model(fl_model, X_test_all, y_test_all, threshold)
    results["centralized"]["global"] = evaluate_model(central_model, X_test_all, y_test_all, threshold)

    # Per-hospital evaluation
    for hid in HOSPITAL_IDS:
        results["federated"]["per_hospital"][hid] = evaluate_model(fl_model,
                                                                   partitions["test"][hid]["X"],
                                                                   partitions["test"][hid]["y"], threshold)
        results["centralized"]["per_hospital"][hid] = evaluate_model(central_model,
                                                                     partitions["test"][hid]["X"],
                                                                     partitions["test"][hid]["y"], threshold)

    # Reporting error analysis
    for hid in HOSPITAL_IDS:
        mask = np.array([m["scenario"] == "reporting_error" for m in partitions["test"][hid]["meta"]])
        if np.any(mask):
            X_err = partitions["test"][hid]["X"][mask]
            y_err = partitions["test"][hid]["y"][mask]
            spike_mask = np.array([m["is_reporting_error"] for m in partitions["test"][hid]["meta"]])[mask]
            results["reporting_error_analysis"][hid] = {
                "all_error_samples": evaluate_model(fl_model, X_err, y_err, threshold),
                "spike_days": evaluate_model(fl_model, X_err[spike_mask] if np.any(spike_mask) else X_err[:0],
                                             y_err[spike_mask] if np.any(spike_mask) else y_err[:0], threshold),
                "n_spikes": int(np.sum(spike_mask))
            }

    out_path = REPORTS_DIR / "fl_simulation.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps({
        "federated_global": results["federated"]["global"],
        "centralized_global": results["centralized"]["global"],
        "report_path": str(out_path)
    }, indent=2))


if __name__ == "__main__":
    main()
