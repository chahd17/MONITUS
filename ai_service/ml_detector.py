#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML-based detector for sustained elevated respiratory-case patterns.
Uses only causal features (past observations). Loads trained model artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import joblib
import numpy as np


class MLDetector:
    """Load and use trained ML detector for sustained outbreak patterns."""

    def __init__(self, model_path: Path = None, scaler_path: Path = None, meta_path: Path = None):
        project_root = Path(__file__).parent.parent
        models_dir = project_root / "models"
        self.model_path = model_path or (models_dir / "ml_outbreak_model.joblib")
        self.scaler_path = scaler_path or (models_dir / "ml_outbreak_scaler.joblib")
        self.meta_path = meta_path or (models_dir / "ml_outbreak_meta.json")

        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        with self.meta_path.open("r", encoding="utf-8") as f:
            self.meta = json.load(f)

        self.feature_names = self.meta["feature_names"]
        self.window_size = self.meta["window_size"]

    def build_causal_features_for_row(self, history_values: List[float]) -> np.ndarray:
        """
        Build causal features using only history (past observations).
        history_values are in chronological order, most recent last.
        Must have >= window_size elements.
        """
        if len(history_values) < self.window_size:
            raise ValueError(f"Need at least {self.window_size} history values")

        hist = np.array(history_values[-self.window_size:], dtype=float)  # last window_size
        features = []

        # Baseline stats from history
        median_hist = np.median(hist)
        mean_hist = np.mean(hist)
        std_hist = np.std(hist, ddof=0) if len(hist) > 0 else 0.0
        mad_hist = np.median(np.abs(hist - median_hist))
        q25 = np.percentile(hist, 25)
        q75 = np.percentile(hist, 75)
        iqr = q75 - q25

        features.append(median_hist)
        features.append(mean_hist)
        features.append(std_hist)
        features.append(mad_hist)
        features.append(q25)
        features.append(q75)
        features.append(iqr)

        # Current vs baseline (but current is the last element? no - features are built from history before current)
        # For prediction at current time t using history t-window_size:t-1? Or including up to t-1
        # We need causal features using current and PAST observations only
        if len(history_values) >= 1:
            current = history_values[-1]
        else:
            current = mean_hist
        features.append(current)
        features.append(current - median_hist)
        features.append((current - median_hist) / (mad_hist * 1.4826 + 1e-8))
        features.append(current / (mean_hist + 1e-8))

        # Recent trends (last 7 days vs earlier)
        if len(hist) >= 14:
            last7 = hist[-7:]
            prev7 = hist[-14:-7]
            features.append(np.mean(last7))
            features.append(np.mean(last7) - np.mean(prev7))
            features.append(np.mean(last7) / (np.mean(prev7) + 1e-8))
        else:
            features.append(np.mean(hist[-min(7, len(hist)):]))
            features.append(0.0)
            features.append(1.0)

        # Growth
        if len(hist) >= 3:
            features.append(hist[-1] - hist[-2])
            features.append(hist[-1] - hist[-3])
        else:
            features.append(0.0)
            features.append(0.0)

        # Variability
        features.append(np.max(hist) - np.min(hist))
        features.append((hist[-1] - hist[0]) / len(hist) if len(hist) > 0 else 0.0)

        return np.array(features).reshape(1, -1)

    def predict_proba(self, history_values: List[float]) -> float:
        """Predict probability of sustained outbreak pattern."""
        X = self.build_causal_features_for_row(history_values)
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0][1]
        return float(proba)

    def predict(self, history_values: List[float], threshold: float = None) -> bool:
        if threshold is None:
            threshold = self.meta.get("threshold", 0.5)
        return self.predict_proba(history_values) >= threshold
