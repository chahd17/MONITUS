#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train a small interpretable ML detector for sustained elevated respiratory-case patterns.
Generates multiple independent synthetic simulations with separate seeds.
Split by whole simulation runs before fitting; synthetic evaluation only.
"""
from __future__ import annotations
from ai_service.ml_features import build_causal_features, get_feature_names

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

# Import generator functions
from scripts.generate_hospital_data import generate_normal, generate_regional_outbreak, generate_reporting_error, HOSPITALS

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path('C:/Users/doudaa/Documents/MONITUS')
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


class MLSyntheticGenerator:
    """Generate multiple independent simulations with separate seeds."""

    def __init__(self):
        self.hospitals = HOSPITALS
        self.days = 90
        self.start_date = date(2024, 1, 1)
        self.window_size = 21  # need >=21 prior days

    def generate_simulation(self, sim_seed: int, scenario_type: str) -> List[Dict]:
        """
        Generate one simulation run with its own seed.
        scenario_type: 'normal', 'outbreak', 'mixed' (for variety)
        """
        rng = random.Random(sim_seed)
        rows = []

        if scenario_type == 'normal':
            # All normal
            for h in self.hospitals:
                baseline = rng.randint(12, 16)
                current_date = self.start_date
                for i in range(self.days):
                    fluct = rng.randint(-3, 3)
                    cases = max(0, baseline + fluct)
                    rows.append({
                        "date": current_date.isoformat(),
                        "hospital_id": h["hospital_id"],
                        "city": h["city"],
                        "respiratory_cases": int(cases),
                        "sim_id": f"sim_{sim_seed}",
                        "sim_seed": sim_seed
                    })
                    current_date += timedelta(days=1)
        elif scenario_type == 'outbreak':
            # Regional outbreak like original
            outbreak_start_offset = self.days - 14
            for h in self.hospitals:
                baseline = rng.randint(12, 16)
                current_date = self.start_date
                for i in range(self.days):
                    if i >= outbreak_start_offset and h["hospital_id"] in ("HOSP_TUN", "HOSP_SOU"):
                        spike = rng.randint(15, 25)
                        cases = max(0, baseline + spike)
                    else:
                        fluct = rng.randint(-2, 2)
                        cases = max(0, baseline + fluct)
                    rows.append({
                        "date": current_date.isoformat(),
                        "hospital_id": h["hospital_id"],
                        "city": h["city"],
                        "respiratory_cases": int(cases),
                        "sim_id": f"sim_{sim_seed}",
                        "sim_seed": sim_seed
                    })
                    current_date += timedelta(days=1)
        elif scenario_type == 'reporting_error':
            # Reporting error as data quality - should be negative for outbreak classification
            spike_hospital = "HOSP_TUN"
            spike_day_offset = rng.randint(10, self.days - 20)
            for h in self.hospitals:
                baseline = rng.randint(12, 16)
                current_date = self.start_date
                for i in range(self.days):
                    if h["hospital_id"] == spike_hospital and i == spike_day_offset:
                        cases = max(0, baseline + rng.randint(80, 120))
                    else:
                        fluct = rng.randint(-2, 2)
                        cases = max(0, baseline + fluct)
                    rows.append({
                        "date": current_date.isoformat(),
                        "hospital_id": h["hospital_id"],
                        "city": h["city"],
                        "respiratory_cases": int(cases),
                        "sim_id": f"sim_{sim_seed}",
                        "sim_seed": sim_seed
                    })
                    current_date += timedelta(days=1)

        return rows






def label_outbreak_day(scenario_type: str, day_idx: int, days_total: int, hospital_id: str) -> int:
    """
    Generator-derived labels. Regional outbreak is sustained increase in last 14 days
    for HOSP_TUN and HOSP_SOU. Reporting error is data quality - label as 0 (negative)
    for outbreak classification. Normal is 0.
    """
    if scenario_type == 'outbreak':
        outbreak_start = days_total - 14
        if day_idx >= outbreak_start and hospital_id in ("HOSP_TUN", "HOSP_SOU"):
            return 1
        return 0
    elif scenario_type == 'reporting_error':
        # Data quality issue, not sustained outbreak - treat as negative
        return 0
    elif scenario_type == 'normal':
        return 0
    return 0



def calculate_event_detection_delays(meta_test, test_pred, y_test):
    """Measure delays for labeled outbreak events, grouped by simulation and hospital."""
    from datetime import date

    groups = {}
    for metadata, prediction, label in zip(meta_test, test_pred, y_test):
        key = (metadata["sim_id"], metadata["hospital_id"])
        groups.setdefault(key, []).append(
            (date.fromisoformat(str(metadata["date"])), int(prediction), int(label))
        )

    delays = []
    missed_events = 0

    for observations in groups.values():
        observations.sort(key=lambda item: item[0])
        onset_dates = [day for day, _, label in observations if label == 1]
        if not onset_dates:
            continue

        onset = onset_dates[0]
        detected_dates = [
            day for day, prediction, _ in observations
            if day >= onset and prediction == 1
        ]

        if detected_dates:
            delays.append((detected_dates[0] - onset).days)
        else:
            missed_events += 1

    return delays, missed_events


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    gen = MLSyntheticGenerator()
    window_size = 21

    # Generate multiple independent simulations with separate seeds
    # Split by whole simulation runs: train/val/test
    train_seeds = [1001, 1002, 1003, 1004, 1005]  # 5 train sims
    val_seeds = [2001, 2002]  # 2 val sims
    test_seeds = [3001, 3002, 3003]  # 3 held-out test sims

    # Mix scenario types
    train_configs = [(s, random.Random(s).choice(['normal', 'outbreak'])) for s in train_seeds]
    val_configs = [(s, random.Random(s+1000).choice(['normal', 'outbreak'])) for s in val_seeds]
    test_configs = [(s, random.Random(s+2000).choice(['normal', 'outbreak'])) for s in test_seeds]

    def collect_data(sim_configs):
        X_list = []
        y_list = []
        meta_list = []
        for sim_seed, scen_type in sim_configs:
            sim_rows = gen.generate_simulation(sim_seed, scen_type)
            # Group by hospital
            by_hosp = {}
            for r in sim_rows:
                hid = r['hospital_id']
                if hid not in by_hosp:
                    by_hosp[hid] = []
                by_hosp[hid].append(r)
            # Sort by date (already in order)
            for hid, hosp_rows in by_hosp.items():
                # Build history
                history = []
                for idx, row in enumerate(hosp_rows):
                    history.append(float(row['respiratory_cases']))
                    # Need >= window_size prior days to make prediction
                    if len(history) >= window_size + 1:  # have history of window_size+1
                        # Use history up to idx (current) for features - causal (all past including current)
                        # Actually use last window_size elements as history window
                        feat_hist = history[-window_size:]
                        X_list.append(build_causal_features(feat_hist, window_size))
                        y_list.append(label_outbreak_day(scen_type, idx, gen.days, hid))
                        meta_list.append({
                            'sim_id': f'sim_{sim_seed}',
                            'sim_seed': sim_seed,
                            'hospital_id': hid,
                            'date': row['date'],
                            'scenario': scen_type
                        })
        return np.array(X_list), np.array(y_list), meta_list


    X_train, y_train, meta_train = collect_data(train_configs)
    X_val, y_val, meta_val = collect_data(val_configs)
    X_test, y_test, meta_test = collect_data(test_configs)

    print(f"Train: {X_train.shape[0]} samples, pos={np.sum(y_train)}, neg={len(y_train)-np.sum(y_train)}")
    print(f"Val: {X_val.shape[0]} samples, pos={np.sum(y_val)}, neg={len(y_val)-np.sum(y_val)}")
    print(f"Test: {X_test.shape[0]} samples, pos={np.sum(y_test)}, neg={len(y_test)-np.sum(y_test)}")
    print(f"Train sims: {[c[0] for c in train_configs]}, Val sims: {[c[0] for c in val_configs]}, Test sims: {[c[0] for c in test_configs]}")

    # Fit scaler on train only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Handle class imbalance
    class_weight = 'balanced'

    clf = LogisticRegression(max_iter=1000, class_weight=class_weight, random_state=42)
    clf.fit(X_train_scaled, y_train)

    # Choose threshold on validation only
    val_proba = clf.predict_proba(X_val_scaled)[:, 1]
    # Try thresholds
    best_thresh = 0.5
    best_f1 = -1
    for thresh in np.arange(0.1, 0.9, 0.05):
        val_pred = (val_proba >= thresh).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(y_val, val_pred, average='binary', zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh
    print(f"Best threshold on val: {best_thresh:.3f} (F1={best_f1:.3f})")

    # Evaluate ONCE on held-out test
    test_proba = clf.predict_proba(X_test_scaled)[:, 1]
    test_pred = (test_proba >= best_thresh).astype(int)
    cm = confusion_matrix(y_test, test_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, test_pred, average='binary', zero_division=0)

    delays, missed_events = calculate_event_detection_delays(meta_test, test_pred, y_test)

    feature_names = get_feature_names()

    # Save artifacts
    joblib.dump(clf, MODELS_DIR / "ml_outbreak_model.joblib")
    joblib.dump(scaler, MODELS_DIR / "ml_outbreak_scaler.joblib")

    meta = {
        "model_type": "LogisticRegression",
        "interpreter": "linear",
        "feature_names": feature_names,
        "window_size": window_size,
        "threshold": float(best_thresh),
        "class_weight": class_weight,
        "train_seeds": train_seeds,
        "val_seeds": val_seeds,
        "test_seeds": test_seeds,
        "train_configs": [(s, c) for s, c in train_configs],
        "val_configs": [(s, c) for s, c in val_configs],
        "test_configs": [(s, c) for s, c in test_configs],
        "random_state": 42,
        "notes": "Trained on disjoint synthetic simulation runs. Scaler fitted on training data; threshold selected on validation data. Reporting errors treated as negative."
    }
    with (MODELS_DIR / "ml_outbreak_meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    eval_report = {
        "title": "MONITUS ML Detector Evaluation (Honest Out-of-Sample)",
        "dataset_sizes": {
            "train": {"n_samples": int(len(X_train)), "n_pos": int(np.sum(y_train)), "n_neg": int(len(y_train)-np.sum(y_train)), "n_sims": len(train_seeds)},
            "val": {"n_samples": int(len(X_val)), "n_pos": int(np.sum(y_val)), "n_neg": int(len(y_val)-np.sum(y_val)), "n_sims": len(val_seeds)},
            "test": {"n_samples": int(len(X_test)), "n_pos": int(np.sum(y_test)), "n_neg": int(len(y_test)-np.sum(y_test)), "n_sims": len(test_seeds)}
        },
        "split_method": "By whole simulation runs (separate seeds). No day-level random split. Train/val/test disjoint.",
        "labels": "Generator-derived: regional outbreak last 14 days for HOSP_TUN/HOSP_SOU = 1; reporting_error and normal = 0 (data-quality treated separately).",
        "features": {"causal": True, "window_size": window_size, "names": feature_names, "notes": "Uses 21 observations including the current day; no later observations are required."},
        "model": {"type": "LogisticRegression", "class_weight": "balanced", "max_iter": 1000, "random_state": 42},
        "threshold_selection": {"method": "chosen on validation runs only", "best_threshold": float(best_thresh), "val_f1_at_best": float(best_f1)},
        "held_out_test_evaluation": {
            "confusion_matrix": {"tn": int(cm[0][0]), "fp": int(cm[0][1]), "fn": int(cm[1][0]), "tp": int(cm[1][1])},
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "n_samples": int(len(X_test))
        },
        "event_detection_delay": {
            "note": "Days from first labeled outbreak observation to first positive prediction on or after onset; detected events only.",
            "delays_days": delays,
            "detected_events": len(delays),
            "missed_events": missed_events,
            "total_outbreak_events": len(delays) + missed_events
        },
        "limitations": [
            "Synthetic data only - no clinical validation",
            "Small number of simulations",
            "Reporting errors treated as negative class",
            "Model not connected to API/dashboard"
        ],
        "artifacts": {
            "model": str(MODELS_DIR / "ml_outbreak_model.joblib"),
            "scaler": str(MODELS_DIR / "ml_outbreak_scaler.joblib"),
            "metadata": str(MODELS_DIR / "ml_outbreak_meta.json")
        },
        "reproducibility": {"seeds_fixed": True, "scaler_fitted_on_train_only": True, "split_by_simulation": True}
    }

    with (REPORTS_DIR / "ml_evaluation.json").open("w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print("\n=== HELD-OUT TEST RESULTS ===")
    print(f"CM: TN={cm[0][0]} FP={cm[0][1]} FN={cm[1][0]} TP={cm[1][1]}")
    print(f"P={prec:.4f} R={rec:.4f} F1={f1:.4f}")
    print(f"Report saved to {REPORTS_DIR / 'ml_evaluation.json'}")


if __name__ == "__main__":
    main()
