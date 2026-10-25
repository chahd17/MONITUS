import unittest

import numpy as np

from ai_service.ml_features import build_causal_features, get_feature_names
from ai_service.ml_detector import MLDetector


class TestMLFeatureConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.detector = MLDetector()

    def test_training_inference_identical(self):
        observations = [20 + (i % 5) for i in range(21)]
        training = build_causal_features(observations, 21)
        inference = self.detector.build_causal_features_for_row(observations)
        np.testing.assert_array_equal(training, inference[0])

    def test_feature_names_match_metadata(self):
        self.assertEqual(self.detector.feature_names, get_feature_names())

    def test_eighteen_features(self):
        features = build_causal_features([25] * 21, 21)
        self.assertEqual(len(features), 18)

    def test_current_observation_is_included(self):
        baseline = [20] * 20
        features_a = build_causal_features(baseline + [20], 21)
        features_b = build_causal_features(baseline + [100], 21)
        self.assertNotEqual(features_a[7], features_b[7])
        self.assertEqual(features_b[7], 100)

    def test_future_observations_not_required(self):
        observations = [20] * 20 + [35]
        current_features = build_causal_features(observations, 21)
        later_features = build_causal_features(observations + [999], 21)
        self.assertEqual(current_features[7], 35)
        self.assertEqual(later_features[7], 999)


if __name__ == "__main__":
    unittest.main()
