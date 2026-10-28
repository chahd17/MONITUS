#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Held-out test evaluation v2 for Step 3.4 (post-review).

Context and integrity notes:
- The first evaluation (reports/fl_simulation.json) already consumed test seeds
  3001-3006. It is preserved unchanged as the historical v1 result and is NOT
  re-used or re-tuned here.
- This v2 evaluation uses PREVIOUSLY UNTOUCHED simulation seeds, chosen by a
  fixed rule BEFORE running: reserved contiguous blocks 4xxx (train), 5xxx
  (validation), 6xxx (test), disjoint from every seed used by Step 3.3 and by
  v1 (1xxx/2xxx/3xxx). The rule was documented before evaluation.
- Hyperparameters and the classification threshold were frozen on
  TRAIN/VALIDATION only by scripts/diagnose_federated_trainval.py and stored in
  reports/fl_frozen_config.json. This script refuses to run without it.
- This follows review of the first test results; that fact is disclosed in the
  generated report.

This is a simulation only. No clinical validity. No formal privacy guarantee
(ordinary FedAvg, no secure aggregation, no differential privacy).
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

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
HISTORICAL_REPORT = REPORTS_DIR / "fl_simulation.json"
FROZEN_CONFIG_PATH = REPORTS_DIR / "fl_frozen_config.json"
OUTPUT_PATH = REPORTS_DIR / "fl_simulation_v2.json"

# Fixed BEFORE evaluation: reserved blocks disjoint from all previously used seeds.
FRESH_SEEDS = {
    "train": [(4001, "normal"), (4002, "outbreak"), (4003, "outbreak"),
              (4004, "outbreak"), (4005, "outbreak"), (4006, "reporting_error"),
              (4007, "reporting_error"), (4008, "reporting_error")],
    "val": [(5001, "outbreak"), (5002, "normal"), (5003, "reporting_error"),
            (5004, "reporting_error"), (5005, "reporting_error")],
    "test": [(6001, "outbreak"), (6002, "outbreak"), (6003, "normal"),
             (6004, "reporting_error"), (6005, "reporting_error"),
             (6006, "reporting_error")],
}
SEED_RULE = (
    "Reserved disjoint contiguous blocks fixed before evaluation: 4xxx train, "
    "5xxx validation, 6xxx test. Disjoint from Step 3.3 and from v1 seeds "
    "(1xxx/2xxx/3xxx). Chosen after review of v1 test results, disclosed."
)


def _metrics(y: np.ndarray, proba: np.ndarray, threshold: float) -> Dict[str, Any]:
    if len(y) == 0:
        return {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "precision": 0.0,
                "recall": 0.0, "f1": 0.0, "accuracy": 0.0, "n_samples": 0}
    pred = (proba >= threshold).astype(int)
    tp = int(np.sum((pred == 1) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": float(precision), "recall": float(recall), "f1": float(f1),
        "accuracy": float((tp + tn) / len(y)), "n_samples": int(len(y)),
    }


def _prob_summary(proba: np.ndarray) -> Dict[str, float]:
    if len(proba) == 0:
        return {}
    return {
        "min": float(np.min(proba)), "p10": float(np.percentile(proba, 10)),
        "p25": float(np.percentile(proba, 25)), "median": float(np.median(proba)),
        "p75": float(np.percentile(proba, 75)), "p90": float(np.percentile(proba, 90)),
        "max": float(np.max(proba)), "mean": float(np.mean(proba)),
    }


def _stable_sigmoid(z: np.ndarray) -> np.ndarray:
    p = np.empty_like(z, dtype=float)
    pos = z >= 0
    p[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    p[~pos] = ez / (1.0 + ez)
    return p


def _grad_norm(params, X, y) -> float:
    coef = np.asarray(params["coef"], dtype=float)
    b = float(np.asarray(params["intercept"]))
    p = _stable_sigmoid(X @ coef + b)
    err = p - y.astype(float)
    g = (X.T @ err) / len(y)
    gb = float(np.mean(err))
    return float(np.sqrt(np.sum(g ** 2) + gb ** 2))


def _train_fl(train_partitions, cfg, collect_val=None) -> Dict[str, Any]:
    clip = cfg["clip"]
    lr = cfg["learning_rate"]
    local_iter = cfg["local_iterations"]
    rounds = cfg["rounds"]
    rs = cfg["random_state"]

    X_by_h = {h: apply_fixed_feature_transform(train_partitions[h]["X"], clip) for h in HOSPITAL_IDS}
    y_by_h = {h: train_partitions[h]["y"] for h in HOSPITAL_IDS}
    clients = {
        h: LocalFederatedClient(
            h, {"X": X_by_h[h], "y": y_by_h[h], "meta": train_partitions[h]["meta"]},
            learning_rate=lr, local_iterations=local_iter, random_state=rs,
        )
        for h in HOSPITAL_IDS
    }
    gm = BinaryLogisticRegression(n_features=18, learning_rate=lr, max_iter=local_iter, random_state=rs)
    gp = gm.get_params()
    history: List[Dict[str, Any]] = []
    for r in range(rounds):
        pre = {"coef": np.array(gp["coef"], copy=True),
               "intercept": np.array(gp["intercept"], copy=True)}
        # weighted train loss / gradient norm at round start (diagnostic only)
        n = {h: int(len(y_by_h[h])) for h in HOSPITAL_IDS}
        total = sum(n.values())
        losses, grads = {}, {}
        for h in HOSPITAL_IDS:
            m = BinaryLogisticRegression(n_features=18, random_state=rs); m.set_params(pre)
            losses[h] = float(m.loss(X_by_h[h], y_by_h[h]))
            grads[h] = _grad_norm(pre, X_by_h[h], y_by_h[h])
        wl = sum(losses[h] * n[h] for h in HOSPITAL_IDS) / total
        wg = sum(grads[h] * n[h] for h in HOSPITAL_IDS) / total

        ups = [clients[h].train_round(gp) for h in HOSPITAL_IDS]
        gp = FederatedAggregator.aggregate(ups)

        entry = {"round": r + 1,
                 "weighted_train_loss_at_round_start": float(wl),
                 "weighted_gradient_norm_at_round_start": float(wg),
                 "per_client_gradient_norm": {h: float(grads[h]) for h in HOSPITAL_IDS}}
        if collect_val is not None:
            Xv = apply_fixed_feature_transform(
                np.vstack([collect_val[h]["X"] for h in HOSPITAL_IDS]), clip)
            yv = np.concatenate([collect_val[h]["y"] for h in HOSPITAL_IDS])
            m = BinaryLogisticRegression(n_features=18, random_state=rs); m.set_params(gp)
            entry["val_loss"] = float(m.loss(Xv, yv))
            entry["val_f1_at_frozen_threshold"] = float(
                _metrics(yv, m.predict_proba(Xv), cfg["threshold"])["f1"])
        history.append(entry)

    model = BinaryLogisticRegression(n_features=18, random_state=rs); model.set_params(gp)
    return {"model": model, "params": gp, "history": history}


def _train_centralized(train_partitions, cfg) -> Dict[str, Any]:
    """Offline benchmark: pool TRAINING data only. Same transform, same lr, and
    the same number of full-batch gradient steps as FL local steps per client."""
    clip = cfg["clip"]
    X = np.vstack([apply_fixed_feature_transform(train_partitions[h]["X"], clip) for h in HOSPITAL_IDS])
    y = np.concatenate([train_partitions[h]["y"] for h in HOSPITAL_IDS])
    budget = int(cfg["rounds"]) * int(cfg["local_iterations"])
    model = BinaryLogisticRegression(
        n_features=18, learning_rate=cfg["learning_rate"], max_iter=budget,
        class_weight=cfg["class_weight"], random_state=cfg["random_state"],
    )
    model.fit(X, y)
    return {"model": model, "params": model.get_params(), "gradient_steps": budget, "n_train": int(len(y))}


def main() -> None:
    if not FROZEN_CONFIG_PATH.exists():
        raise SystemExit(
            "Frozen config missing. Run scripts/diagnose_federated_trainval.py first "
            "(train/validation only)."
        )
    with FROZEN_CONFIG_PATH.open(encoding="utf-8") as f:
        cfg = json.load(f)
    # Guardrail: the frozen config must not have been selected on test.
    if cfg.get("selected_on_test") is not False:
        raise SystemExit("Frozen config is not explicitly marked selected_on_test=False; refusing to run.")

    partitions = partition_hospital_data(sim_configs_by_split=FRESH_SEEDS)
    threshold = float(cfg["threshold"])
    clip = cfg["clip"]

    fl = _train_fl(partitions["train"], cfg, collect_val=partitions["val"])
    fl_model = fl["model"]
    central = _train_centralized(partitions["train"], cfg)

    # ---- Evaluate ONCE on fresh held-out test --------------------------------
    X_test = {h: apply_fixed_feature_transform(partitions["test"][h]["X"], clip) for h in HOSPITAL_IDS}
    y_test = {h: partitions["test"][h]["y"] for h in HOSPITAL_IDS}
    X_test_all = np.vstack([X_test[h] for h in HOSPITAL_IDS])
    y_test_all = np.concatenate([y_test[h] for h in HOSPITAL_IDS])

    def eval_all(model):
        proba_all = model.predict_proba(X_test_all)
        global_m = _metrics(y_test_all, proba_all, threshold)
        per_h, per_h_proba = {}, {}
        for h in HOSPITAL_IDS:
            ph = model.predict_proba(X_test[h])
            per_h[h] = _metrics(y_test[h], ph, threshold)
            per_h_proba[h] = _prob_summary(ph)
        return global_m, per_h, per_h_proba, proba_all

    fl_global, fl_per_h, fl_proba_h, fl_proba_all = eval_all(fl_model)
    cen_global, cen_per_h, cen_proba_h, cen_proba_all = eval_all(central["model"])

    # Per-class probabilities on held-out test.
    pos = y_test_all == 1
    per_class_proba = {
        "federated": {"positive": _prob_summary(fl_proba_all[pos]),
                      "negative": _prob_summary(fl_proba_all[~pos])},
        "centralized": {"positive": _prob_summary(cen_proba_all[pos]),
                        "negative": _prob_summary(cen_proba_all[~pos])},
        "n_positive": int(np.sum(pos)), "n_negative": int(np.sum(~pos)),
    }

    # ---- reporting_error analysis --------------------------------------------
    reporting = {}
    for h in HOSPITAL_IDS:
        metas = partitions["test"][h]["meta"]
        scen = np.array([m["scenario"] == "reporting_error" for m in metas])
        spike = np.array([bool(m.get("is_reporting_error", False)) for m in metas])
        entry = {"n_error_scenario": int(np.sum(scen)), "n_spike_days": int(np.sum(spike))}
        if np.any(scen):
            idx = scen
            entry["federated_error_scenario"] = _metrics(
                y_test[h][idx], fl_model.predict_proba(X_test[h][idx]), threshold)
            entry["centralized_error_scenario"] = _metrics(
                y_test[h][idx], central["model"].predict_proba(X_test[h][idx]), threshold)
        if np.any(spike):
            idx = spike
            entry["federated_spike_days"] = _metrics(
                y_test[h][idx], fl_model.predict_proba(X_test[h][idx]), threshold)
            entry["centralized_spike_days"] = _metrics(
                y_test[h][idx], central["model"].predict_proba(X_test[h][idx]), threshold)
        reporting[h] = entry

    # False-positive behavior on the normal scenario.
    fp_normal = {}
    for h in HOSPITAL_IDS:
        metas = partitions["test"][h]["meta"]
        normal = np.array([m["scenario"] == "normal" for m in metas])
        if np.any(normal):
            fp_normal[h] = {
                "federated": _metrics(y_test[h][normal],
                                      fl_model.predict_proba(X_test[h][normal]), threshold),
                "centralized": _metrics(y_test[h][normal],
                                        central["model"].predict_proba(X_test[h][normal]), threshold),
            }

    historical_status = "preserved unchanged" if HISTORICAL_REPORT.exists() else "not found"

    report = {
        "version": "v2",
        "supersedes_for_current_findings": None,
        "historical_report": {
            "path": "reports/fl_simulation.json",
            "status": historical_status,
            "note": ("v1 evaluated already-consumed test seeds 3001-3006 and is kept "
                     "unchanged as history. v2 does NOT replace it."),
        },
        "disclosure": (
            "This v2 evaluation was produced AFTER and IN RESPONSE TO review of the "
            "first (v1) test results. v1 test seeds were never re-used or re-tuned."
        ),
        "seed_rule": SEED_RULE,
        "fresh_seeds": FRESH_SEEDS,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script": "scripts/eval_federated_v2.py",
            "frozen_config_path": "reports/fl_frozen_config.json",
            "frozen_config": cfg,
            "threshold": threshold,
            "normalization": (
                f"fixed winsorisation of robust_zscore (index {ROBUST_ZSCORE_FEATURE_INDEX}) "
                "to +/-" + (str(clip) if clip is not None else "none") +
                "; NOT fitted, NOT privacy-preserving"
            ),
            "feature_count": 18,
            "window_size": 21,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "test_evaluated_once": True,
            "optimization_budget": {
                "federated": {
                    "rounds": cfg["rounds"],
                    "local_iterations_per_client_per_round": cfg["local_iterations"],
                    "total_local_gradient_steps_per_client": int(cfg["rounds"]) * int(cfg["local_iterations"]),
                },
                "centralized": {"full_batch_gradient_steps": central["gradient_steps"],
                                "n_train_samples": central["n_train"]},
            },
        },
        "privacy_warning": (
            "ORDINARY FEDAVG HAS NO FORMAL PRIVACY GUARANTEE, NO SECURE AGGREGATION, "
            "AND NO DIFFERENTIAL PRIVACY. Model updates can leak information about "
            "local data. This is a simulation only."
        ),
        "clinical_warning": (
            "NOT READY FOR CLINICAL OR PRODUCTION USE. Synthetic data and a simple "
            "linear model; no outbreak-detection claim."
        ),
        "partition_summary": {
            split: {h: {"n_samples": int(partitions[split][h]["n_samples"]),
                        "n_pos": int(np.sum(partitions[split][h]["y"])),
                        "n_neg": int(partitions[split][h]["n_samples"] - np.sum(partitions[split][h]["y"])),
                        "sim_ids": sorted({m["sim_id"] for m in partitions[split][h]["meta"]})}
                    for h in HOSPITAL_IDS}
            for split in ["train", "val", "test"]
        },
        "convergence_history": fl["history"],
        "federated": {"global": fl_global, "per_hospital": fl_per_h,
                      "per_hospital_probabilities": fl_proba_h},
        "centralized": {"global": cen_global, "per_hospital": cen_per_h,
                        "per_hospital_probabilities": cen_proba_h},
        "per_class_probabilities_test": per_class_proba,
        "reporting_error_analysis": reporting,
        "normal_scenario_false_positives": fp_normal,
        "limitations": [
            "Simulation only; synthetic data.",
            "No formal privacy guarantee (ordinary FedAvg; no secure aggregation, no DP).",
            "Fixed winsorisation selected on validation; not a privacy mechanism.",
            "Unweighted BCE; the Sfax client is all-negative in training.",
            "Overlapping, correlated windows.",
            "Single linear model; no clinical claim.",
        ],
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    print(json.dumps({
        "federated_global": fl_global,
        "centralized_global": cen_global,
        "threshold": threshold,
        "report_path": str(OUTPUT_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
