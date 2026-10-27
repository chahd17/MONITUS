#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Federated data partitioning utilities for MONITUS Step 3.4 (micro-step 2).
Builds per-hospital partitions from synthetic simulations with full isolation.

Notes:
- This is only a federated simulation; no formal privacy guarantee (no secure aggregation, no differential privacy).
- Do not fit a global scaler on pooled private hospital data here.
- Reuses same 18 causal features and 21-observation warmup as Step 3.3.
- Preserves full-simulation train/validation/test separation.
- Reporting error samples treated as negative (0) like Step 3.3.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
import copy

import numpy as np

from ai_service.ml_features import build_causal_features, get_feature_names
from scripts.train_ml_detector import (
    MLSyntheticGenerator,
    get_simulation_configs,
    validate_simulation_splits,
    label_outbreak_day,
    HOSPITALS,
)


FEATURE_NAMES = get_feature_names()
WINDOW_SIZE = 21
HOSPITAL_IDS = [h["hospital_id"] for h in HOSPITALS]


def _validate_partition_inputs(sim_configs_by_split: Dict[str, List[Tuple[int, str]]]):
    """Validate simulation configs for leakage."""
    if not isinstance(sim_configs_by_split, dict):
        raise ValueError("sim_configs_by_split must be a dict")
    required = {"train", "val", "test"}
    if set(sim_configs_by_split.keys()) != required:
        raise ValueError(f"Must contain exactly {sorted(required)}")
    # Reuse existing validation
    validate_simulation_splits(sim_configs_by_split)


def partition_hospital_data(
    sim_configs_by_split: Optional[Dict[str, List[Tuple[int, str]]]] = None,
    generator: Optional[MLSyntheticGenerator] = None,
    window_size: int = WINDOW_SIZE,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Construct local hospital partitions per split.

    Returns structure:
    {
      "train": {
        "HOSP_TUN": {"X": np.array, "y": np.array, "meta": [...], "n_samples": int},
        ...
      },
      "val": {...},
      "test": {...}
    }

    Each partition contains only its hospital's data. No raw records pooled across
    hospitals in this function. Provenance metadata includes sim_id, sim_seed,
    hospital_id, date, scenario, split, is_reporting_error.
    """
    if sim_configs_by_split is None:
        sim_configs_by_split = get_simulation_configs()
    _validate_partition_inputs(sim_configs_by_split)

    gen = generator if generator is not None else MLSyntheticGenerator()
    if gen.window_size != window_size:
        # Allow override but warn via behavior
        pass

    result = {}
    for split in ["train", "val", "test"]:
        result[split] = {}
        for hid in HOSPITAL_IDS:
            result[split][hid] = {
                "X": [],
                "y": [],
                "meta": [],
            }

    # Track seen (sim_seed, split) for auditing
    all_seen_seeds = set()

    for split in ["train", "val", "test"]:
        for sim_seed, scen_type in sim_configs_by_split[split]:
            if sim_seed in all_seen_seeds:
                raise ValueError(f"Simulation seed reused: {sim_seed}")
            all_seen_seeds.add(sim_seed)
            # Generate simulation
            rows = gen.generate_simulation(sim_seed, scen_type)
            # Group by hospital
            by_hosp = {}
            for row in rows:
                by_hosp.setdefault(row["hospital_id"], []).append(row)
            # Process each hospital separately
            for hid in HOSPITAL_IDS:
                if hid not in by_hosp:
                    continue
                hosp_rows = sorted(by_hosp[hid], key=lambda r: r["date"])
                history = []
                for idx, row in enumerate(hosp_rows):
                    history.append(float(row["respiratory_cases"]))
                    if len(history) >= window_size:
                        X_feat = build_causal_features(history, window_size)
                        y_label = label_outbreak_day(scen_type, idx, gen.days, hid)
                        # Validate feature shape
                        if X_feat.shape[0] != len(FEATURE_NAMES):
                            raise ValueError(f"Feature dimension mismatch: {X_feat.shape[0]} != {len(FEATURE_NAMES)}")
                        if not np.all(np.isfinite(X_feat)):
                            raise ValueError("Non-finite feature values detected")
                        result[split][hid]["X"].append(X_feat)
                        result[split][hid]["y"].append(int(y_label))
                        result[split][hid]["meta"].append({
                            "sim_id": f"sim_{sim_seed}",
                            "sim_seed": int(sim_seed),
                            "hospital_id": hid,
                            "date": row["date"],
                            "scenario": scen_type,
                            "split": split,
                            "is_reporting_error": bool(row.get("is_reporting_error", False)),
                        })

    # Convert to arrays
    final_result = {}
    for split in ["train", "val", "test"]:
        final_result[split] = {}
        for hid in HOSPITAL_IDS:
            X_list = result[split][hid]["X"]
            y_list = result[split][hid]["y"]
            meta_list = result[split][hid]["meta"]
            if len(X_list) == 0:
                final_result[split][hid] = {
                    "X": np.array([]).reshape(0, len(FEATURE_NAMES)),
                    "y": np.array([], dtype=int),
                    "meta": [],
                    "n_samples": 0,
                }
            else:
                X_arr = np.array(X_list)
                y_arr = np.array(y_list, dtype=int)
                # Validate alignment
                if X_arr.shape[0] != y_arr.shape[0] or X_arr.shape[0] != len(meta_list):
                    raise ValueError("Sample alignment mismatch")
                final_result[split][hid] = {
                    "X": X_arr,
                    "y": y_arr,
                    "meta": meta_list,
                    "n_samples": int(X_arr.shape[0]),
                }

    return final_result


def get_partition_summary(partitions: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    """Get summary of partitions."""
    summary = {}
    for split in ["train", "val", "test"]:
        summary[split] = {}
        for hid in HOSPITAL_IDS:
            p = partitions[split][hid]
            y = p["y"]
            summary[split][hid] = {
                "n_samples": p["n_samples"],
                "n_pos": int(np.sum(y)) if len(y) > 0 else 0,
                "n_neg": int(len(y) - np.sum(y)) if len(y) > 0 else 0,
                "sim_ids": sorted(list(set(m["sim_id"] for m in p["meta"]))),
            }
    return summary


# Fixed, explicitly documented transformation (no scaler fitted on pooled private data).
#
# The shared Step 3.3 feature "robust_zscore" divides by the median absolute
# deviation. When MAD is ~0 this feature explodes (train/validation std ~6e6),
# which destroys gradient-descent optimisation. We therefore apply a fixed
# winsorisation (clip) to that single feature. The clip bound is a predefined
# constant chosen from a small candidate set using TRAIN/VALIDATION only; it is
# NOT fitted on pooled private data and it is NOT a privacy mechanism.
ROBUST_ZSCORE_FEATURE_INDEX = FEATURE_NAMES.index("robust_zscore")
FIXED_ROBUST_ZSCORE_CLIP = 5.0

FIXED_TRANSFORMATION_CONSTANTS = {
    "description": (
        "Fixed winsorisation of the robust_zscore feature (index "
        f"{ROBUST_ZSCORE_FEATURE_INDEX}). Not fitted on data; not a privacy mechanism."
    ),
    "method": "clip",
    "feature": "robust_zscore",
    "feature_index": ROBUST_ZSCORE_FEATURE_INDEX,
    "lower": -FIXED_ROBUST_ZSCORE_CLIP,
    "upper": FIXED_ROBUST_ZSCORE_CLIP,
    "mean": None,   # no fitted mean
    "scale": None,  # no fitted scale
    "fitted": False,
    "privacy_preserving": False,
    "candidate_bounds": [3.0, 5.0, 10.0],
    "default_bound": FIXED_ROBUST_ZSCORE_CLIP,
    "applied": False,  # applied explicitly by orchestration scripts, not implicitly
}


def apply_fixed_feature_transform(X, clip: Optional[float] = None) -> np.ndarray:
    """Apply the fixed robust_zscore winsorisation to a feature matrix.

    ``clip=None`` disables the transform (returns a copy of the input).
    No statistic is fitted, so no pooled hospital data is required.
    """
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError("X must be 2-dimensional (n_samples, n_features)")
    if X.shape[1] != len(FEATURE_NAMES):
        raise ValueError(f"X must have {len(FEATURE_NAMES)} features")
    if not np.all(np.isfinite(X)):
        raise ValueError("X contains non-finite values")
    out = X.copy()
    if clip is not None:
        if not np.isfinite(clip) or clip <= 0:
            raise ValueError("clip must be a positive finite number or None")
        out[:, ROBUST_ZSCORE_FEATURE_INDEX] = np.clip(
            out[:, ROBUST_ZSCORE_FEATURE_INDEX], -float(clip), float(clip)
        )
    return out
