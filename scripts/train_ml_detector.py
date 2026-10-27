#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train a small interpretable ML detector for sustained elevated respiratory-case patterns.
Generates multiple independent synthetic simulations with separate seeds.
Split by whole simulation runs before fitting; synthetic evaluation only.
"""
from __future__ import annotations
from ai_service.ml_features import build_causal_features, get_feature_names

import json
import platform
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from scripts.generate_hospital_data import HOSPITALS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


class MLSyntheticGenerator:
    """Generate multiple independent simulations with separate seeds."""

    def __init__(self):
        self.hospitals = HOSPITALS
        self.days = 90
        self.start_date = date(2024, 1, 1)
        self.window_size = 21  # 20 previous observations plus today's observation

    def generate_simulation(self, sim_seed: int, scenario_type: str) -> List[Dict]:
        """
        Generate one simulation run with its own seed.
        scenario_type: 'normal', 'outbreak', or 'reporting_error'.
        Counts describe fictional aggregated hospital reports, not patient records.
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
            # A one-day batch/entry error, followed by a return to baseline.
            # Vary hospital, date and magnitude independently for each run. Include
            # moderate spikes overlapping outbreak counts, not only extreme errors.
            spike_hospital = rng.choice(self.hospitals)["hospital_id"]
            spike_day_offset = rng.randint(self.window_size - 1, self.days - self.window_size)
            spike_size = rng.randint(15, 120)
            for h in self.hospitals:
                baseline = rng.randint(12, 16)
                current_date = self.start_date
                for i in range(self.days):
                    if h["hospital_id"] == spike_hospital and i == spike_day_offset:
                        cases = max(0, baseline + spike_size)
                    else:
                        fluct = rng.randint(-2, 2)
                        cases = max(0, baseline + fluct)
                    rows.append({
                        "date": current_date.isoformat(),
                        "hospital_id": h["hospital_id"],
                        "city": h["city"],
                        "respiratory_cases": int(cases),
                        "sim_id": f"sim_{sim_seed}",
                        "sim_seed": sim_seed,
                        "is_reporting_error": h["hospital_id"] == spike_hospital and i == spike_day_offset
                    })
                    current_date += timedelta(days=1)

        else:
            raise ValueError(f"Unknown synthetic scenario: {scenario_type}")
        return rows


def get_simulation_configs():
    """Fixed whole-run splits, chosen before fitting or measuring performance.

    Preserve the existing normal/outbreak runs and add independent error runs to
    every split. Never reuse a simulation seed, including across scenario types.
    """
    return {
        "train": [(1001, "normal"), (1002, "outbreak"), (1003, "outbreak"),
                  (1004, "outbreak"), (1005, "outbreak"),
                  (1006, "reporting_error"), (1007, "reporting_error"), (1008, "reporting_error")],
        "val": [(2001, "outbreak"), (2002, "normal"),
                (2003, "reporting_error"), (2004, "reporting_error"), (2005, "reporting_error")],
        "test": [(3001, "outbreak"), (3002, "outbreak"), (3003, "normal"),
                 (3004, "reporting_error"), (3005, "reporting_error"), (3006, "reporting_error")],
    }


def validate_simulation_splits(configs):
    """Reject reused seeds and missing scenarios before generating any samples."""
    seen = set()
    for split in ("train", "val", "test"):
        scenarios = set()
        for seed, scenario in configs[split]:
            if seed in seen:
                raise ValueError(f"Simulation seed reused: {seed}")
            seen.add(seed)
            scenarios.add(scenario)
        if scenarios != {"normal", "outbreak", "reporting_error"}:
            raise ValueError(f"Split {split} must include all three synthetic scenarios")


def collect_data(sim_configs, window_size=21, generator=None):
    """Build same-day samples starting at observation 21 (including today).

    History is reset for every simulation/hospital. Labels and error-event flags
    are evaluation metadata only; the shared feature function receives counts.
    """
    gen = generator if generator is not None else MLSyntheticGenerator()
    X_list, y_list, meta_list = [], [], []
    for sim_seed, scen_type in sim_configs:
        by_hosp = {}
        for row in gen.generate_simulation(sim_seed, scen_type):
            by_hosp.setdefault(row['hospital_id'], []).append(row)
        for hid, hosp_rows in by_hosp.items():
            hosp_rows.sort(key=lambda row: row['date'])
            history = []
            for idx, row in enumerate(hosp_rows):
                history.append(float(row['respiratory_cases']))
                if len(history) >= window_size:
                    X_list.append(build_causal_features(history, window_size))
                    y_list.append(label_outbreak_day(scen_type, idx, gen.days, hid))
                    meta_list.append({
                        'sim_id': f'sim_{sim_seed}',
                        'sim_seed': sim_seed,
                        'hospital_id': hid,
                        'date': row['date'],
                        'scenario': scen_type,
                        'is_reporting_error': row.get('is_reporting_error', False),
                    })
    return np.array(X_list), np.array(y_list), meta_list


def summarize_dataset(y, metadata, configs):
    """Count actual scored samples, including coverage of error spike days."""
    summary = {
        "n_samples": int(len(y)), "n_pos": int(np.sum(y)),
        "n_neg": int(len(y) - np.sum(y)), "n_sims": len(configs),
        "scenarios": {},
    }
    for scenario in ("normal", "outbreak", "reporting_error"):
        mask = np.array([row['scenario'] == scenario for row in metadata])
        labels = y[mask]
        summary["scenarios"][scenario] = {
            "n_sims": sum(kind == scenario for _, kind in configs),
            "n_samples": int(len(labels)), "n_pos": int(np.sum(labels)),
            "n_neg": int(len(labels) - np.sum(labels)),
            "n_error_spikes": sum(row['is_reporting_error'] for row in metadata if row['scenario'] == scenario),
        }
    return summary


def classification_metrics(labels, predictions):
    """Use a fixed binary matrix even for all-negative reporting-error runs."""
    cm = confusion_matrix(labels, predictions, labels=[0, 1])
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='binary', zero_division=0
    )
    return {
        "confusion_matrix": {"tn": int(cm[0, 0]), "fp": int(cm[0, 1]),
                             "fn": int(cm[1, 0]), "tp": int(cm[1, 1])},
        "precision": float(precision), "recall": float(recall), "f1": float(f1),
        "n_samples": int(len(labels)),
        "false_positive_rate": float(cm[0, 1] / max(1, cm[0, 0] + cm[0, 1])),
    }


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
    configs = get_simulation_configs()
    validate_simulation_splits(configs)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    gen = MLSyntheticGenerator()
    window_size = gen.window_size
    train_configs, val_configs, test_configs = (configs[split] for split in ("train", "val", "test"))
    train_seeds, val_seeds, test_seeds = ([seed for seed, _ in runs] for runs in (train_configs, val_configs, test_configs))

    X_train, y_train, meta_train = collect_data(train_configs, window_size, gen)
    X_val, y_val, meta_val = collect_data(val_configs, window_size, gen)
    X_test, y_test, meta_test = collect_data(test_configs, window_size, gen)

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

    # Evaluate the fixed model/threshold on held-out runs; do not tune on test.
    test_proba = clf.predict_proba(X_test_scaled)[:, 1]
    test_pred = (test_proba >= best_thresh).astype(int)
    test_metrics = classification_metrics(y_test, test_pred)
    by_scenario = {}
    for scenario in ("normal", "outbreak", "reporting_error"):
        mask = np.array([row['scenario'] == scenario for row in meta_test])
        by_scenario[scenario] = classification_metrics(y_test[mask], test_pred[mask])
    error_mask = np.array([row['is_reporting_error'] for row in meta_test])
    error_spike_metrics = classification_metrics(y_test[error_mask], test_pred[error_mask])

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
        "window_semantics": "20 previous observations plus today's observation; first sample at observation 21",
        "threshold": float(best_thresh),
        "class_weight": class_weight,
        "train_seeds": train_seeds,
        "val_seeds": val_seeds,
        "test_seeds": test_seeds,
        "train_configs": [(s, c) for s, c in train_configs],
        "val_configs": [(s, c) for s, c in val_configs],
        "test_configs": [(s, c) for s, c in test_configs],
        "random_state": 42,
        "software_versions": {"python": platform.python_version(), "numpy": np.__version__,
                              "scikit-learn": sklearn.__version__, "joblib": joblib.__version__},
        "notes": "Synthetic simulations only, including independent reporting-error runs in every split, labeled non-outbreak. Scaler fitted on training data; threshold selected on validation data. Scores do not establish clinical performance."
    }
    with (MODELS_DIR / "ml_outbreak_meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    eval_report = {
        "title": "MONITUS ML Detector Evaluation (Held-out Synthetic Runs Only)",
        "dataset_sizes": {
            "train": summarize_dataset(y_train, meta_train, train_configs),
            "val": summarize_dataset(y_val, meta_val, val_configs),
            "test": summarize_dataset(y_test, meta_test, test_configs),
        },
        "simulation_configs": configs,
        "split_method": "By whole simulation runs (separate seeds). No day-level random split. Train/val/test disjoint.",
        "labels": "Generator-derived: outbreak last 14 days for HOSP_TUN/HOSP_SOU = 1; normal and all reporting_error days = 0. The classifier does not diagnose data-quality issues.",
        "reporting_error_design": "One isolated one-day batch/entry spike per run, random fictional hospital, day index 20..69, additional count 15..120, then baseline. Three independent runs per split; event flags are evaluation metadata, never features.",
        "features": {"causal": True, "window_size": window_size, "names": feature_names, "notes": "Uses 21 observations including the current day; first sample at observation 21. Same-day detection, not future forecasting. No later observations are required."},
        "model": {"type": "LogisticRegression", "class_weight": "balanced", "max_iter": 1000, "random_state": 42},
        "threshold_selection": {"method": "chosen on validation runs only", "best_threshold": float(best_thresh), "val_f1_at_best": float(best_f1)},
        "held_out_test_evaluation": test_metrics,
        "held_out_test_by_scenario": by_scenario,
        "held_out_reporting_error_spikes": error_spike_metrics,
        "metric_notes": "Precision/recall/F1 use zero_division=0. All-negative scenarios have no positive-class recall to estimate; inspect their FP counts/rates. Samples overlap within runs and are not independent clinical observations.",
        "event_detection_delay": {
            "note": "Days from first labeled outbreak observation to first positive prediction on or after onset; detected events only.",
            "delays_days": delays,
            "detected_events": len(delays),
            "missed_events": missed_events,
            "total_outbreak_events": len(delays) + missed_events
        },
        "limitations": [
            "Synthetic data only - no clinical validation",
            "Small fixed set of simulations from one simplified generator family; held-out seeds do not establish real-world generalization",
            "Only one isolated reporting spike per error run; no missing reports, multi-day backlogs or mixed outbreak/error events",
            "Moderate reporting spikes overlap outbreak counts; same-day features cannot always distinguish causes",
            "Reporting errors labeled negative by design, not identified as data-quality alerts by this classifier",
            "Overlapping windows are correlated; metrics are descriptive and have no confidence intervals",
            "Existing test seeds were inspected in a previous review cycle; these results are not a fresh external validation",
            "Model not connected to API/dashboard"
        ],
        "artifacts": {
            "model": "models/ml_outbreak_model.joblib",
            "scaler": "models/ml_outbreak_scaler.joblib",
            "metadata": "models/ml_outbreak_meta.json"
        },
        "reproducibility": {"seeds_fixed": True, "scaler_fitted_on_train_only": True, "split_by_simulation": True}
    }

    with (REPORTS_DIR / "ml_evaluation.json").open("w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    print("\n=== HELD-OUT TEST RESULTS ===")
    cm = test_metrics['confusion_matrix']
    print(f"CM: TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")
    print(f"P={test_metrics['precision']:.4f} R={test_metrics['recall']:.4f} F1={test_metrics['f1']:.4f}")
    print("Reporting-error spike days:", json.dumps(error_spike_metrics))
    print(f"Report saved to {REPORTS_DIR / 'ml_evaluation.json'}")


if __name__ == "__main__":
    main()
