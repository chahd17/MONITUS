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
from ai_service.ml_features import build_causal_features


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
        """Build features from the latest window, including today's observation."""
        features = build_causal_features(history_values, self.window_size)
        return features.reshape(1, -1)

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
