"""Regression coverage for real training samples and regenerated ML artifacts."""
import json
import random
import unittest
from datetime import timedelta

import numpy as np

from ai_service.ml_detector import MLDetector
from scripts import train_ml_detector as training


class TestMLTrainingPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = training.get_simulation_configs()
        cls.datasets = {split: training.collect_data(runs) for split, runs in cls.configs.items()}
        cls.detector = MLDetector()

    def test_all_splits_include_scored_negative_reporting_errors(self):
        training.validate_simulation_splits(self.configs)
        for split, (X, y, metadata) in self.datasets.items():
            with self.subTest(split=split):
                self.assertEqual({row['scenario'] for row in metadata},
                                 {'normal', 'outbreak', 'reporting_error'})
                error_seeds = {seed for seed, kind in self.configs[split] if kind == 'reporting_error'}
                spike_rows = [i for i, row in enumerate(metadata) if row['is_reporting_error']]
                self.assertGreater(len(error_seeds), 0)
                self.assertEqual({metadata[i]['sim_seed'] for i in spike_rows}, error_seeds)
                self.assertEqual(len(spike_rows), len(error_seeds))
                for i, row in enumerate(metadata):
                    if row['scenario'] == 'reporting_error':
                        self.assertEqual(y[i], 0)
                # The spikes themselves, not just normal days from error runs,
                # must reach the actual feature matrix used for fitting/scoring.
                self.assertTrue(np.all(X[spike_rows, 7] >= 27))

    def test_error_runs_are_seeded_independent_and_isolated(self):
        gen = training.MLSyntheticGenerator()
        global_state = random.getstate()
        signatures = set()
        for configs in self.configs.values():
            for seed, scenario in configs:
                if scenario != 'reporting_error':
                    continue
                rows = gen.generate_simulation(seed, scenario)
                self.assertEqual(rows, gen.generate_simulation(seed, scenario))
                self.assertEqual(len(rows), 270)
                spikes = [row for row in rows if row['is_reporting_error']]
                self.assertEqual(len(spikes), 1)
                spike = spikes[0]
                first_scored = (gen.start_date + timedelta(days=20)).isoformat()
                last_spike = (gen.start_date + timedelta(days=69)).isoformat()
                self.assertGreaterEqual(spike['date'], first_scored)
                self.assertLessEqual(spike['date'], last_spike)
                self.assertGreaterEqual(spike['respiratory_cases'], 27)
                self.assertLessEqual(spike['respiratory_cases'], 136)
                for row in rows:
                    self.assertIsInstance(row['respiratory_cases'], int)
                    if not row['is_reporting_error']:
                        self.assertGreaterEqual(row['respiratory_cases'], 10)
                        self.assertLessEqual(row['respiratory_cases'], 18)
                signatures.add(tuple(row['respiratory_cases'] for row in rows))
        self.assertEqual(len(signatures), 9)
        self.assertEqual(random.getstate(), global_state)

    def test_actual_simulations_are_separate_across_splits(self):
        seen = set()
        for split, (_, _, metadata) in self.datasets.items():
            ids = {row['sim_id'] for row in metadata}
            self.assertEqual(ids, {f'sim_{seed}' for seed, _ in self.configs[split]})
            self.assertFalse(seen & ids)
            seen.update(ids)

    def test_reused_seed_across_splits_is_rejected_even_for_another_scenario(self):
        configs = training.get_simulation_configs()
        configs['test'].append((1001, 'reporting_error'))
        with self.assertRaisesRegex(ValueError, 'seed reused'):
            training.validate_simulation_splits(configs)

    def test_reused_seed_within_split_is_rejected(self):
        configs = training.get_simulation_configs()
        configs['train'].append(configs['train'][0])
        with self.assertRaisesRegex(ValueError, 'seed reused'):
            training.validate_simulation_splits(configs)

    def test_missing_error_scenario_is_rejected(self):
        configs = training.get_simulation_configs()
        configs['val'] = [(seed, kind) for seed, kind in configs['val'] if kind != 'reporting_error']
        with self.assertRaisesRegex(ValueError, 'all three'):
            training.validate_simulation_splits(configs)

    def test_unknown_generator_scenario_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown synthetic scenario'):
            training.MLSyntheticGenerator().generate_simulation(1, 'typo')

    def test_first_sample_is_observation_21_in_both_paths(self):
        for split, (X, _, metadata) in self.datasets.items():
            self.assertEqual(X.shape, (len(self.configs[split]) * 210, 18))
            for seed, _ in self.configs[split]:
                for hospital in training.HOSPITALS:
                    samples = [row for row in metadata if row['sim_seed'] == seed
                               and row['hospital_id'] == hospital['hospital_id']]
                    self.assertEqual(len(samples), 70)
                    self.assertEqual(samples[0]['date'], '2024-01-21')
                    self.assertEqual(samples[-1]['date'], '2024-03-30')
        with self.assertRaises(ValueError):
            self.detector.predict_proba([15] * 20)
        self.assertTrue(np.isfinite(self.detector.predict_proba([15] * 21)))

    def test_every_collected_feature_vector_matches_inference(self):
        gen = training.MLSyntheticGenerator()
        for split, (X, _, metadata) in self.datasets.items():
            histories = {}
            for seed, scenario in self.configs[split]:
                for row in gen.generate_simulation(seed, scenario):
                    histories.setdefault((seed, row['hospital_id']), []).append(row)
            for vector, meta in zip(X, metadata):
                history = [row['respiratory_cases'] for row in histories[(meta['sim_seed'], meta['hospital_id'])]
                           if row['date'] <= meta['date']]
                inference = self.detector.build_causal_features_for_row(history)
                np.testing.assert_array_equal(vector, inference[0])

    def test_histories_reset_between_simulations(self):
        runs = [(1001, 'normal'), (1006, 'reporting_error')]
        combined_X, combined_y, combined_meta = training.collect_data(runs)
        for index, run in enumerate(runs):
            X, y, metadata = training.collect_data([run])
            section = slice(index * 210, (index + 1) * 210)
            np.testing.assert_array_equal(combined_X[section], X)
            np.testing.assert_array_equal(combined_y[section], y)
            self.assertEqual(combined_meta[section], metadata)

    def test_future_counts_do_not_change_earlier_training_samples(self):
        class ChangedFuture(training.MLSyntheticGenerator):
            def generate_simulation(self, seed, scenario):
                rows = super().generate_simulation(seed, scenario)
                for row in rows:
                    if row['date'] > '2024-01-21':
                        row['respiratory_cases'] = 999
                return rows

        runs = [(1001, 'normal')]
        before, _, _ = training.collect_data(runs)
        after, _, _ = training.collect_data(runs, generator=ChangedFuture())
        # First scored day of each hospital is unaffected by later reports.
        np.testing.assert_array_equal(before[[0, 70, 140]], after[[0, 70, 140]])
        self.assertFalse(np.array_equal(before[1], after[1]))

    def test_error_flags_are_not_features(self):
        class HiddenFlags(training.MLSyntheticGenerator):
            def generate_simulation(self, seed, scenario):
                rows = super().generate_simulation(seed, scenario)
                for row in rows:
                    row.pop('is_reporting_error', None)
                return rows

        runs = [(1006, 'reporting_error')]
        X, y, _ = training.collect_data(runs)
        hidden_X, hidden_y, _ = training.collect_data(runs, generator=HiddenFlags())
        np.testing.assert_array_equal(X, hidden_X)
        np.testing.assert_array_equal(y, hidden_y)

    def test_all_negative_metrics_keep_binary_matrix(self):
        metrics = training.classification_metrics([0, 0, 0], [0, 1, 0])
        self.assertEqual(metrics['confusion_matrix'], {'tn': 2, 'fp': 1, 'fn': 0, 'tp': 0})
        self.assertAlmostEqual(metrics['false_positive_rate'], 1 / 3)
        self.assertEqual(metrics['f1'], 0.0)


class TestRegeneratedMLArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = training.get_simulation_configs()
        cls.datasets = {split: training.collect_data(runs) for split, runs in cls.configs.items()}
        cls.detector = MLDetector()
        cls.report = json.loads((training.REPORTS_DIR / 'ml_evaluation.json').read_text(encoding='utf-8'))

    def test_saved_configs_and_coverage_match_generated_samples(self):
        for split, (X, y, metadata) in self.datasets.items():
            expected_configs = [list(run) for run in self.configs[split]]
            self.assertEqual(self.report['simulation_configs'][split], expected_configs)
            self.assertEqual(self.detector.meta[f'{split}_configs'], expected_configs)
            self.assertEqual(self.detector.meta[f'{split}_seeds'], [seed for seed, _ in self.configs[split]])
            self.assertEqual(self.report['dataset_sizes'][split],
                             training.summarize_dataset(y, metadata, self.configs[split]))
            self.assertEqual(X.shape[1], 18)

    def test_saved_scaler_was_fitted_to_training_samples_only(self):
        X, _, _ = self.datasets['train']
        self.assertEqual(self.detector.scaler.n_samples_seen_, len(X))
        np.testing.assert_allclose(self.detector.scaler.mean_, X.mean(axis=0))
        np.testing.assert_allclose(self.detector.scaler.var_, X.var(axis=0))
        self.assertEqual(self.detector.model.n_features_in_, 18)

    def test_saved_threshold_matches_validation_only_selection(self):
        X, y, _ = self.datasets['val']
        probabilities = self.detector.model.predict_proba(self.detector.scaler.transform(X))[:, 1]
        candidates = np.arange(0.1, 0.9, 0.05)
        scores = [training.classification_metrics(y, (probabilities >= threshold).astype(int))['f1']
                  for threshold in candidates]
        index = int(np.argmax(scores))
        self.assertEqual(self.detector.meta['threshold'], candidates[index])
        self.assertEqual(self.report['threshold_selection']['best_threshold'], candidates[index])
        self.assertEqual(self.report['threshold_selection']['val_f1_at_best'], scores[index])

    def test_saved_test_metrics_match_artifact_predictions(self):
        X, y, metadata = self.datasets['test']
        probabilities = self.detector.model.predict_proba(self.detector.scaler.transform(X))[:, 1]
        predictions = (probabilities >= self.detector.meta['threshold']).astype(int)
        self.assertEqual(self.report['held_out_test_evaluation'], training.classification_metrics(y, predictions))
        for scenario in ('normal', 'outbreak', 'reporting_error'):
            mask = np.array([row['scenario'] == scenario for row in metadata])
            self.assertEqual(self.report['held_out_test_by_scenario'][scenario],
                             training.classification_metrics(y[mask], predictions[mask]))
        mask = np.array([row['is_reporting_error'] for row in metadata])
        self.assertEqual(self.report['held_out_reporting_error_spikes'],
                         training.classification_metrics(y[mask], predictions[mask]))
        delays, missed = training.calculate_event_detection_delays(metadata, predictions, y)
        self.assertEqual(self.report['event_detection_delay']['delays_days'], delays)
        self.assertEqual(self.report['event_detection_delay']['missed_events'], missed)
        self.assertEqual(self.report['event_detection_delay']['total_outbreak_events'], len(delays) + missed)


if __name__ == '__main__':
    unittest.main()
