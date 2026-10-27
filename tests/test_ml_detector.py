#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ML detector - causal features, labeling, run separation, model loading."""
import json
import unittest
from pathlib import Path

import numpy as np
import joblib

from ai_service.ml_detector import MLDetector
from scripts import train_ml_detector


class TestMLDetector(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.models_dir = self.project_root / "models"
        self.reports_dir = self.project_root / "reports"

    def test_model_artifacts_exist(self):
        self.assertTrue((self.models_dir / "ml_outbreak_model.joblib").exists())
        self.assertTrue((self.models_dir / "ml_outbreak_scaler.joblib").exists())
        self.assertTrue((self.models_dir / "ml_outbreak_meta.json").exists())
        self.assertTrue((self.reports_dir / "ml_evaluation.json").exists())

    def test_meta_has_required_fields(self):
        with (self.models_dir / "ml_outbreak_meta.json").open() as f:
            meta = json.load(f)
        for key in ["model_type", "feature_names", "window_size", "threshold",
                    "train_seeds", "val_seeds", "test_seeds"]:
            self.assertIn(key, meta)
        # Check run separation
        all_seeds = set(meta["train_seeds"]) | set(meta["val_seeds"]) | set(meta["test_seeds"])
        self.assertEqual(len(all_seeds), len(meta["train_seeds"]) + len(meta["val_seeds"]) + len(meta["test_seeds"]))

    def test_causal_features_no_future(self):
        # Build features from history only
        hist = [15, 16, 14, 17, 15, 16, 15, 14, 16, 17, 15, 16, 14, 15, 16, 17, 15, 14, 16, 15, 20]
        feats = train_ml_detector.build_causal_features(hist)
        self.assertEqual(len(feats), len(train_ml_detector.get_feature_names()))
        self.assertIsInstance(feats, np.ndarray)
        # Features should be finite
        for f in feats:
            self.assertTrue(np.isfinite(f))

    def test_labeling_generator_derived(self):
        # Outbreak last 14 days for TUN/SOU
        self.assertEqual(train_ml_detector.label_outbreak_day('outbreak', 75, 90, 'HOSP_TUN'), 0)
        self.assertEqual(train_ml_detector.label_outbreak_day('outbreak', 76, 90, 'HOSP_TUN'), 1)
        self.assertEqual(train_ml_detector.label_outbreak_day('outbreak', 89, 90, 'HOSP_SOU'), 1)
        self.assertEqual(train_ml_detector.label_outbreak_day('outbreak', 89, 90, 'HOSP_SFX'), 0)
        # Reporting error negative for outbreak
        self.assertEqual(train_ml_detector.label_outbreak_day('reporting_error', 50, 90, 'HOSP_TUN'), 0)
        self.assertEqual(train_ml_detector.label_outbreak_day('normal', 50, 90, 'HOSP_TUN'), 0)

    def test_run_separation_no_overlap(self):
        with (self.models_dir / "ml_outbreak_meta.json").open() as f:
            meta = json.load(f)
        train = set(meta["train_seeds"])
        val = set(meta["val_seeds"])
        test = set(meta["test_seeds"])
        self.assertEqual(len(train & val), 0)
        self.assertEqual(len(train & test), 0)
        self.assertEqual(len(val & test), 0)

    def test_deterministic_reproducibility(self):
        gen = train_ml_detector.MLSyntheticGenerator()
        rows1 = gen.generate_simulation(12345, 'outbreak')
        rows2 = gen.generate_simulation(12345, 'outbreak')
        self.assertEqual(len(rows1), len(rows2))
        self.assertEqual(rows1[0]['respiratory_cases'], rows2[0]['respiratory_cases'])

    def test_prediction_structure(self):
        det = MLDetector()
        hist = [15] * 25  # enough history
        proba = det.predict_proba(hist)
        self.assertIsInstance(proba, float)
        self.assertGreaterEqual(proba, 0.0)
        self.assertLessEqual(proba, 1.0)
        pred = det.predict(hist)
        self.assertIsInstance(pred, bool)

    def test_evaluation_report_structure(self):
        with (self.reports_dir / "ml_evaluation.json").open() as f:
            rep = json.load(f)
        self.assertIn('dataset_sizes', rep)
        self.assertIn('held_out_test_evaluation', rep)
        self.assertIn('split_method', rep)
        self.assertIn('confusion_matrix', rep['held_out_test_evaluation'])
        for k in ['train', 'val', 'test']:
            self.assertIn(k, rep['dataset_sizes'])


if __name__ == '__main__':
    unittest.main()
