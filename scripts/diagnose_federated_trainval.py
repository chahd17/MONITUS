#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAIN/VALIDATION-ONLY diagnostics and hyperparameter selection for Step 3.4.

This script never touches the test split. It:
  1. Summarises feature magnitudes on TRAIN only.
  2. Grid-searches a small, predefined set of hyperparameters
     (robust_zscore clip, learning rate, local iterations, rounds) using
     TRAIN for fitting and VALIDATION for selection.
  3. Selects a classification threshold on VALIDATION only.
  4. Records real training/validation losses, per-round diagnostics,
     probability distributions, per-class metrics and gradient norms.
  5. Writes reports/fl_trainval_diagnostics.json and a frozen configuration
     reports/fl_frozen_config.json to be consumed by the held-out evaluation.

No pooled private training data is used to fit a federated scaler: the only
preprocessing is a fixed winsorisation whose bound is selected on validation.

This is a simulation only. No clinical validity and no formal privacy guarantee.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ai_service.fl_model import BinaryLogisticRegression
from ai_service.fl_client import LocalFederatedClient
from ai_service.fl_server import FederatedAggregator
from ai_service.fl_utils import (
    partition_hospital_data,
    apply_fixed_feature_transform,
    ROBUST_ZSCORE_FEATURE_INDEX,
    HOSPITAL_IDS,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
THRESHOLD_GRID = np.round(np.arange(0.05, 0.951, 0.01), 2)


def _metrics_from_proba(y: np.ndarray, proba: np.ndarray, threshold: float) -> Dict[str, Any]:
    pred = (proba >= threshold).astype(int)
    tp = int(np.sum((pred == 1) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y) if len(y) else 0.0
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": float(precision), "recall": float(recall),
        "f1": float(f1), "accuracy": float(accuracy),
        "n_samples": int(len(y)),
    }


def _prob_summary(proba: np.ndarray) -> Dict[str, float]:
    if len(proba) == 0:
        return {}
    return {
        "min": float(np.min(proba)),
        "p10": float(np.percentile(proba, 10)),
        "p25": float(np.percentile(proba, 25)),
        "median": float(np.median(proba)),
        "p75": float(np.percentile(proba, 75)),
        "p90": float(np.percentile(proba, 90)),
        "max": float(np.max(proba)),
        "mean": float(np.mean(proba)),
    }


def _feature_summary(X: np.ndarray) -> List[Dict[str, float]]:
    return [
        {
            "index": i,
            "min": float(np.min(X[:, i])),
            "max": float(np.max(X[:, i])),
            "mean": float(np.mean(X[:, i])),
            "std": float(np.std(X[:, i])),
        }
        for i in range(X.shape[1])
    ]


def _per_client_gradient_norm(params: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> float:
    """Gradient norm of the global BCE at a client's local data (diagnostic only).

    Computed locally for diagnostics; no raw data is sent to the server.
    """
    coef = np.asarray(params["coef"], dtype=float)
    intercept = float(np.asarray(params["intercept"]))
    z = X @ coef + intercept
    # Numerically stable sigmoid
    p = np.empty_like(z, dtype=float)
    pos = z >= 0
    p[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    p[~pos] = ez / (1.0 + ez)
    err = p - y.astype(float)
    g = (X.T @ err) / len(y)
    g_b = float(np.mean(err))
    return float(np.sqrt(np.sum(g ** 2) + g_b ** 2))


def _train_federated(
    train_partitions: Dict[str, Any],
    clip: Optional[float],
    learning_rate: float,
    local_iterations: int,
    rounds: int,
    random_state: int = RANDOM_STATE,
    collect_round_diagnostics: bool = False,
    val_partitions: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Train FedAvg on train partitions. Optionally collect per-round diagnostics."""
    X_by_h = {
        hid: apply_fixed_feature_transform(train_partitions[hid]["X"], clip)
        for hid in HOSPITAL_IDS
    }
    y_by_h = {hid: train_partitions[hid]["y"] for hid in HOSPITAL_IDS}

    clients = {
        hid: LocalFederatedClient(
            hid,
            {
                "X": X_by_h[hid],
                "y": y_by_h[hid],
                "meta": train_partitions[hid]["meta"],
            },
            learning_rate=learning_rate,
            local_iterations=local_iterations,
            random_state=random_state,
        )
        for hid in HOSPITAL_IDS
    }

    global_model = BinaryLogisticRegression(
        n_features=18, learning_rate=learning_rate,
        max_iter=local_iterations, random_state=random_state,
    )
    global_params = global_model.get_params()

    diagnostics: List[Dict[str, Any]] = []
    for round_num in range(rounds):
        # Gradients + local losses at the current global params (before local steps)
        round_grad_norms = {}
        round_train_losses = {}
        pre_params = {
            "coef": np.array(global_params["coef"], copy=True),
            "intercept": np.array(global_params["intercept"], copy=True),
        }
        for hid in HOSPITAL_IDS:
            round_grad_norms[hid] = _per_client_gradient_norm(pre_params, X_by_h[hid], y_by_h[hid])
            mdl = BinaryLogisticRegression(n_features=18, random_state=random_state)
            mdl.set_params(pre_params)
            round_train_losses[hid] = float(mdl.loss(X_by_h[hid], y_by_h[hid]))

        updates = [clients[hid].train_round(global_params) for hid in HOSPITAL_IDS]
        global_params = FederatedAggregator.aggregate(updates)

        if collect_round_diagnostics:
            n_by_h = {hid: int(y_by_h[hid].shape[0]) for hid in HOSPITAL_IDS}
            total_n = sum(n_by_h.values())
            weighted_train_loss = sum(
                round_train_losses[hid] * n_by_h[hid] for hid in HOSPITAL_IDS
            ) / total_n
            weighted_grad_norm = sum(
                round_grad_norms[hid] * n_by_h[hid] for hid in HOSPITAL_IDS
            ) / total_n
            entry: Dict[str, Any] = {
                "round": round_num + 1,
                "weighted_train_loss_before_local_steps": float(weighted_train_loss),
                "weighted_gradient_norm_before_local_steps": float(weighted_grad_norm),
                "per_client_gradient_norm": {k: float(v) for k, v in round_grad_norms.items()},
                "per_client_train_loss": {k: float(v) for k, v in round_train_losses.items()},
                "aggregate_weights_n_samples": {hid: n_by_h[hid] / total_n for hid in HOSPITAL_IDS},
            }
            if val_partitions is not None:
                X_val = apply_fixed_feature_transform(
                    np.vstack([val_partitions[hid]["X"] for hid in HOSPITAL_IDS]), clip
                )
                y_val = np.concatenate([val_partitions[hid]["y"] for hid in HOSPITAL_IDS])
                mdl = BinaryLogisticRegression(n_features=18, random_state=random_state)
                mdl.set_params(global_params)
                entry["val_loss"] = float(mdl.loss(X_val, y_val))
                entry["val_f1_at_0.5"] = float(
                    _metrics_from_proba(y_val, mdl.predict_proba(X_val), 0.5)["f1"]
                )
                entry["val_recall_at_0.5"] = float(
                    _metrics_from_proba(y_val, mdl.predict_proba(X_val), 0.5)["recall"]
                )
            diagnostics.append(entry)

    return global_params, diagnostics


def _select_threshold(y: np.ndarray, proba: np.ndarray) -> Tuple[float, Dict[str, Any]]:
    best = None
    for t in THRESHOLD_GRID:
        m = _metrics_from_proba(y, proba, float(t))
        key = (m["f1"], -abs(float(t) - 0.5))
        if best is None or key > best[0]:
            best = (key, float(t), m)
    return best[1], best[2]


def main() -> None:
    np.random.seed(RANDOM_STATE)
    partitions = partition_hospital_data()

    # ---- TRAIN-only feature magnitude summary ---------------------------------
    X_train_all = np.vstack([partitions["train"][hid]["X"] for hid in HOSPITAL_IDS])
    y_train_all = np.concatenate([partitions["train"][hid]["y"] for hid in HOSPITAL_IDS])
    X_val_all = np.vstack([partitions["val"][hid]["X"] for hid in HOSPITAL_IDS])
    y_val_all = np.concatenate([partitions["val"][hid]["y"] for hid in HOSPITAL_IDS])

    feature_summary = _feature_summary(X_train_all)

    # ---- Grid search on TRAIN fit / VALIDATION selection ----------------------
    clip_candidates: List[Optional[float]] = [None, 10.0, 5.0, 3.0]
    lr_candidates = [0.01, 0.1, 0.5]
    iter_candidates = [20, 100]
    rounds_candidates = [5, 10, 20]

    grid_results: List[Dict[str, Any]] = []
    for clip in clip_candidates:
        X_val_c = apply_fixed_feature_transform(X_val_all, clip)
        for lr in lr_candidates:
            for local_iter in iter_candidates:
                for rounds in rounds_candidates:
                    params, _ = _train_federated(
                        partitions["train"], clip, lr, local_iter, rounds
                    )
                    mdl = BinaryLogisticRegression(n_features=18, random_state=RANDOM_STATE)
                    mdl.set_params(params)
                    proba = mdl.predict_proba(X_val_c)
                    val_loss = float(mdl.loss(X_val_c, y_val_all))
                    val_f1_05 = _metrics_from_proba(y_val_all, proba, 0.5)["f1"]
                    thr, thr_metrics = _select_threshold(y_val_all, proba)
                    grid_results.append({
                        "clip": clip,
                        "learning_rate": lr,
                        "local_iterations": local_iter,
                        "rounds": rounds,
                        "val_loss": val_loss,
                        "val_f1_at_0.5": float(val_f1_05),
                        "selected_threshold": thr,
                        "val_f1_at_selected_threshold": float(thr_metrics["f1"]),
                        "val_precision_at_selected_threshold": float(thr_metrics["precision"]),
                        "val_recall_at_selected_threshold": float(thr_metrics["recall"]),
                    })

    # Deterministic selection: highest val F1 (tuned threshold), then lowest val
    # loss, then fewer rounds, then smaller learning rate, then larger clip bound.
    def rank_key(r: Dict[str, Any]):
        clip_rank = 1e9 if r["clip"] is None else -float(r["clip"])
        return (
            -r["val_f1_at_selected_threshold"],
            r["val_loss"],
            r["rounds"],
            r["learning_rate"],
            clip_rank,
        )

    grid_results.sort(key=rank_key)
    selected = grid_results[0]

    # ---- Final diagnostics for the selected configuration --------------------
    selected_params, round_diag = _train_federated(
        partitions["train"],
        selected["clip"],
        selected["learning_rate"],
        selected["local_iterations"],
        selected["rounds"],
        collect_round_diagnostics=True,
        val_partitions=partitions["val"],
    )

    X_val_sel = apply_fixed_feature_transform(X_val_all, selected["clip"])
    selected_model = BinaryLogisticRegression(n_features=18, random_state=RANDOM_STATE)
    selected_model.set_params(selected_params)
    val_proba = selected_model.predict_proba(X_val_sel)
    threshold = selected["selected_threshold"]
    val_metrics = _metrics_from_proba(y_val_all, val_proba, threshold)
    val_metrics_at_05 = _metrics_from_proba(y_val_all, val_proba, 0.5)
    val_loss = float(selected_model.loss(X_val_sel, y_val_all))

    per_hospital_val = {}
    for hid in HOSPITAL_IDS:
        Xh = apply_fixed_feature_transform(partitions["val"][hid]["X"], selected["clip"])
        yh = partitions["val"][hid]["y"]
        probah = selected_model.predict_proba(Xh)
        per_hospital_val[hid] = {
            "at_selected_threshold": _metrics_from_proba(yh, probah, threshold),
            "at_0.5": _metrics_from_proba(yh, probah, 0.5),
            "probabilities": _prob_summary(probah),
        }

    # Per-class probability distributions on validation.
    pos_mask = y_val_all == 1
    per_class_proba = {
        "positive": _prob_summary(val_proba[pos_mask]),
        "negative": _prob_summary(val_proba[~pos_mask]),
        "n_positive": int(np.sum(pos_mask)),
        "n_negative": int(np.sum(~pos_mask)),
    }

    frozen_config = {
        "clip": selected["clip"],
        "learning_rate": selected["learning_rate"],
        "local_iterations": selected["local_iterations"],
        "rounds": selected["rounds"],
        "threshold": threshold,
        "random_state": RANDOM_STATE,
        "class_weight": None,
        "n_features": 18,
        "window_size": 21,
        "selection_data": "TRAIN fit / VALIDATION selection only (test split never loaded)",
        "selected_on_test": False,
        "selected_at": datetime.now(timezone.utc).isoformat(),
    }

    diagnostics = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script": "scripts/diagnose_federated_trainval.py",
            "split_used": "train/validation ONLY (test split not generated)",
            "random_state": RANDOM_STATE,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "feature_count": 18,
            "window_size": 21,
            "normalization": (
                "fixed winsorisation of robust_zscore (index "
                f"{ROBUST_ZSCORE_FEATURE_INDEX}); NOT fitted, NOT privacy-preserving"
            ),
        },
        "partition_summary": {
            "train": {hid: {"n_samples": int(partitions["train"][hid]["n_samples"]),
                            "n_pos": int(np.sum(partitions["train"][hid]["y"]))}
                      for hid in HOSPITAL_IDS},
            "val": {hid: {"n_samples": int(partitions["val"][hid]["n_samples"]),
                          "n_pos": int(np.sum(partitions["val"][hid]["y"]))}
                    for hid in HOSPITAL_IDS},
        },
        "class_distribution": {
            "train": {"n": int(len(y_train_all)), "n_pos": int(np.sum(y_train_all)),
                      "n_neg": int(len(y_train_all) - np.sum(y_train_all)),
                      "positive_rate": float(np.mean(y_train_all))},
            "val": {"n": int(len(y_val_all)), "n_pos": int(np.sum(y_val_all)),
                    "n_neg": int(len(y_val_all) - np.sum(y_val_all)),
                    "positive_rate": float(np.mean(y_val_all))},
        },
        "feature_magnitude_summary_train": feature_summary,
        "feature_magnitude_flags": [
            {"index": ROBUST_ZSCORE_FEATURE_INDEX, "feature": "robust_zscore",
             "std": feature_summary[ROBUST_ZSCORE_FEATURE_INDEX]["std"],
             "note": "Extreme scale when MAD ~ 0; motivates fixed winsorisation."}
        ],
        "grid_results": grid_results,
        "selected_configuration": frozen_config,
        "selection_rule": (
            "Highest validation F1 at a validation-selected threshold; tie-break by "
            "lower validation loss, then fewer rounds, then smaller learning rate, "
            "then larger clip bound. Deterministic and test-free."
        ),
        "selected_config_validation": {
            "val_loss": val_loss,
            "at_selected_threshold": val_metrics,
            "at_0.5": val_metrics_at_05,
            "per_hospital": per_hospital_val,
            "per_class_probabilities": per_class_proba,
        },
        "round_diagnostics_selected_config": round_diag,
        "fixed_defaults_not_selected": {
            "class_weight": None,
            "note": ("Unweighted BCE because the Sfax client is all-negative in training; "
                     "class_weight='balanced' was not tuned."),
            "random_state": RANDOM_STATE,
            "feature_count": 18,
            "window_size": 21,
        },
        "limitations": [
            "Simulation only; synthetic data.",
            "No formal privacy guarantee (ordinary FedAvg).",
            "The fixed clip bound is a hyperparameter selected on validation, not a privacy mechanism.",
            "Windows overlap and are correlated.",
            "No class weighting; Sfax is all-negative in training.",
        ],
    }

    for path, payload in [
        (REPORTS_DIR / "fl_trainval_diagnostics.json", diagnostics),
        (REPORTS_DIR / "fl_frozen_config.json", frozen_config),
    ]:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")

    print(json.dumps({
        "selected_configuration": frozen_config,
        "val_metrics_at_selected_threshold": val_metrics,
        "val_loss": val_loss,
        "n_grid_points": len(grid_results),
    }, indent=2))


if __name__ == "__main__":
    main()
