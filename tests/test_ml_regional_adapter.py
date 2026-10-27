"""Adapter contracts on handcrafted data, not held-out ML performance tuning."""
import copy
import hashlib
import unittest
from datetime import date, timedelta
from pathlib import Path

from ai_service.ml_detector import MLDetector
from ai_service.ml_regional_adapter import MLRegionalAssessmentAdapter


class StubDetector:
    """Deterministic injected probabilities to test routing, not classification."""
    window_size = 21

    def __init__(self):
        self.meta = {'threshold': 0.65}
        self.calls = []

    def predict_proba(self, history):
        self.calls.append(list(history))
        return 0.9 if history[-1] >= 50 else 0.1


def observations(hospital='A', sim='run', days=24, positives=()):
    return [
        {'sim_id': sim, 'hospital_id': hospital, 'city': 'Fictional city',
         'date': (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
         'respiratory_cases': 100 if i in positives else 10}
        for i in range(days)
    ]


class TestMLRegionalAdapter(unittest.TestCase):
    def setUp(self):
        self.detector = StubDetector()
        self.adapter = MLRegionalAssessmentAdapter(self.detector)

    def assess(self, rows):
        return self.adapter.assess(rows)['run']

    def test_one_site_reporting_error_stays_local(self):
        rows = observations(positives=[20]) + observations('B')
        result = self.assess(rows)
        positives = [s for records in result['local_signals'].values() for s in records if s['anomaly_flag']]
        self.assertEqual(len(positives), 1)
        self.assertEqual(positives[0]['predicted_probability'], 0.9)
        self.assertEqual(result['regional_signals'], [])
        self.assertEqual([a['status'] for a in result['assessments']], ['ISOLATED_ANOMALY'])

    def test_one_hospital_repeated_positive_dates_never_meet_quorum(self):
        rows = observations(positives=[20, 21, 22, 23])
        result = self.assess(rows + rows)
        self.assertEqual(result['regional_signals'], [])
        self.assertEqual(len(result['assessments']), 4)
        self.assertTrue(all(a['status'] == 'ISOLATED_ANOMALY' for a in result['assessments']))
        self.assertTrue(all(a['num_supporting_sites'] == 1 for a in result['assessments']))

    def test_different_date_positives_do_not_combine(self):
        result = self.assess(observations(positives=[20]) + observations('B', positives=[21]))
        self.assertEqual(result['regional_signals'], [])
        self.assertEqual([a['status'] for a in result['assessments']], ['ISOLATED_ANOMALY'] * 2)

    def test_same_day_quorum_is_unconfirmed_without_persistence(self):
        result = self.assess(observations(positives=[20]) + observations('B', positives=[20]))
        self.assertEqual(len(result['regional_signals']), 1)
        report = result['regional_signals'][0]
        self.assertEqual(report['supporting_hospitals'], ['A', 'B'])
        self.assertEqual(report['num_supporting_sites'], 2)
        self.assertEqual(result['assessments'][0]['status'], 'REGIONAL_SIGNAL_UNCONFIRMED')

    def test_persistent_same_day_quorum_requires_review_not_confirmation(self):
        result = self.assess(observations(positives=[20, 21]) + observations('B', positives=[20, 21]))
        self.assertEqual([a['status'] for a in result['assessments']],
                         ['REGIONAL_SIGNAL_UNCONFIRMED', 'REGIONAL_SIGNAL_REQUIRES_REVIEW'])
        self.assertEqual(result['assessments'][1]['evidence_dates'], ['2024-01-21', '2024-01-22'])
        self.assertIn('NOT a confirmed outbreak', result['assessments'][1]['explanation'])
        self.assertFalse(result['confirmed_outbreak'])
        self.assertTrue(all(not a['confirmed_outbreak'] for a in result['assessments']))

    def test_persistence_counts_two_of_three_calendar_days(self):
        result = self.assess(observations(positives=[20, 22]) + observations('B', positives=[20, 22]))
        self.assertEqual(result['assessments'][-1]['status'], 'REGIONAL_SIGNAL_REQUIRES_REVIEW')
        self.assertEqual(result['assessments'][-1]['evidence_dates'], ['2024-01-21', '2024-01-23'])

    def test_old_regional_day_outside_three_day_window_does_not_persist(self):
        result = self.assess(observations(positives=[20, 23]) + observations('B', positives=[20, 23]))
        self.assertEqual(result['assessments'][-1]['status'], 'REGIONAL_SIGNAL_UNCONFIRMED')
        self.assertEqual(result['assessments'][-1]['evidence_dates'], ['2024-01-24'])

    def test_duplicate_days_cannot_fill_warmup(self):
        rows = observations(days=20, positives=[19])
        result = self.assess(rows * 3)
        self.assertEqual(result['local_signals']['A'], [])
        self.assertEqual(result['regional_reports'], [])
        self.assertEqual(self.detector.calls, [])
        self.assertEqual(len(result['input_warnings']), 20)
        self.assertTrue(all(w['ignored_records'] == 2 for w in result['input_warnings']))

    def test_duplicate_scored_day_counts_once_and_is_visible(self):
        rows = observations(days=21, positives=[20])
        result = self.assess(rows + [rows[-1]] * 4)
        self.assertEqual(len(result['local_signals']['A']), 1)
        self.assertEqual(result['regional_reports'][0]['num_supporting_sites'], 1)
        self.assertEqual(result['input_warnings'], [
            {'hospital_id': 'A', 'date': '2024-01-21', 'reason': 'identical_duplicates_ignored',
             'ignored_records': 4}
        ])
        self.assertEqual(len(self.detector.calls), 1)

    def test_conflicting_duplicate_counts_or_city_are_rejected(self):
        rows = observations()
        for change in [{'respiratory_cases': 200}, {'city': 'Different fictional city'}]:
            with self.subTest(change=change):
                duplicate = dict(rows[-1], **change)
                with self.assertRaisesRegex(ValueError, 'Conflicting duplicate'):
                    self.assess(rows + [duplicate])

    def test_missing_day_restarts_only_affected_hospital_warmup(self):
        rows = observations(days=43, positives=[20, 41])
        rows += [r for i, r in enumerate(observations('B', days=43, positives=[20, 41])) if i != 20]
        result = self.assess(rows)
        self.assertEqual(result['local_signals']['A'][0]['date'], '2024-01-21')
        self.assertEqual(result['local_signals']['B'][0]['date'], '2024-02-11')
        self.assertEqual([a['status'] for a in result['assessments']],
                         ['ISOLATED_ANOMALY', 'REGIONAL_SIGNAL_UNCONFIRMED'])
        self.assertIn({'hospital_id': 'B', 'date': '2024-01-22',
                       'reason': 'history_reset_after_calendar_gap'}, result['input_warnings'])

    def test_future_counts_and_new_hospitals_cannot_change_earlier_results(self):
        rows = observations(positives=[20, 21]) + observations('B', positives=[20, 21])
        before = self.assess(rows)
        later = copy.deepcopy(rows)
        for row in later:
            if row['date'] > '2024-01-22':
                row['respiratory_cases'] = 999
        later += observations('C', days=25, positives=[24])[22:]
        after = self.assess(later)
        for key in ['regional_reports', 'regional_signals', 'assessments']:
            earlier = lambda result: [r for r in result[key] if r['date'] <= '2024-01-22']
            self.assertEqual(earlier(before), earlier(after))
        for hid in ['A', 'B']:
            self.assertEqual([s for s in before['local_signals'][hid] if s['date'] <= '2024-01-22'],
                             [s for s in after['local_signals'][hid] if s['date'] <= '2024-01-22'])

    def test_same_date_hospitals_in_different_simulations_cannot_meet_quorum(self):
        rows = observations('A', sim='one', positives=[20]) + observations('B', sim='two', positives=[20])
        results = self.adapter.assess(rows)
        self.assertEqual(set(results), {'one', 'two'})
        for sim_id, result in results.items():
            self.assertEqual(result['regional_signals'], [])
            self.assertEqual(result['assessments'][0]['status'], 'ISOLATED_ANOMALY')
            self.assertEqual(result['assessments'][0]['sim_id'], sim_id)

    def test_histories_do_not_cross_simulation_or_call_boundaries(self):
        rows = observations(sim='one', days=20) + observations(sim='two', days=21, positives=[20])[20:]
        results = self.adapter.assess(rows)
        self.assertTrue(all(r['local_signals']['A'] == [] for r in results.values()))
        self.assertEqual(self.detector.calls, [])
        self.assertEqual(self.adapter.assess(observations(days=20))['run']['local_signals']['A'], [])
        self.assertEqual(self.adapter.assess(observations(days=21)[20:])['run']['local_signals']['A'], [])

    def test_persistence_cannot_cross_simulations(self):
        rows = []
        for sim, positive_day in [('one', 20), ('two', 21)]:
            rows += observations('A', sim=sim, positives=[positive_day])
            rows += observations('B', sim=sim, positives=[positive_day])
        results = self.adapter.assess(rows)
        for result in results.values():
            self.assertEqual([a['status'] for a in result['assessments']], ['REGIONAL_SIGNAL_UNCONFIRMED'])

    def test_chronological_windows_include_today_and_only_latest_21_counts(self):
        rows = observations(days=23)
        for i, row in enumerate(rows):
            row['respiratory_cases'] = i
        self.assess(reversed(rows))
        self.assertEqual(self.detector.calls, [list(range(21)), list(range(1, 22)), list(range(2, 23))])

    def test_order_invariance_and_input_records_are_not_modified(self):
        rows = observations(positives=[20]) + observations('B', positives=[20])
        original = copy.deepcopy(rows)
        self.assertEqual(self.assess(rows), self.assess(reversed(rows)))
        self.assertEqual(rows, original)

    def test_provenance_is_explicit_and_no_statistical_scores_are_invented(self):
        result = self.assess(observations(positives=[20]) + observations('B', positives=[20]))
        forbidden = {'mad', 'baseline_median', 'anomaly_score', 'individual_anomaly_scores'}

        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & value.keys())
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        check(result)
        report = result['regional_signals'][0]
        for signal in report['supporting_hospital_details'].values():
            self.assertEqual(signal['source'], 'ml')
            self.assertEqual(signal['predicted_probability'], 0.9)
            self.assertEqual(signal['threshold'], 0.65)
            self.assertFalse(signal['confirmed_outbreak'])
        self.assertEqual(report['source'], 'ml')
        self.assertEqual(result['assessments'][0]['source'], 'ml')

    def test_negative_or_unscored_days_are_not_regional_reports(self):
        result = self.assess(observations())
        self.assertEqual(len(result['local_signals']['A']), 4)
        self.assertTrue(all(not s['anomaly_flag'] for s in result['local_signals']['A']))
        self.assertEqual(result['regional_reports'], [])
        self.assertEqual(result['assessments'], [])
        self.assertEqual(self.adapter.assess([]), {})

    def test_threshold_is_read_from_detector_and_equality_is_positive(self):
        self.detector.meta['threshold'] = 0.9
        adapter = MLRegionalAssessmentAdapter(self.detector)
        result = adapter.assess(observations(days=21, positives=[20]))['run']
        self.assertEqual(result['threshold'], 0.9)
        self.assertTrue(result['local_signals']['A'][0]['anomaly_flag'])

    def test_invalid_input_records_are_rejected(self):
        changes = [{'sim_id': None}, {'sim_id': ''}, {'hospital_id': ''},
                   {'date': '20240101'}, {'date': '2024-02-30'}, {'date': None},
                   {'respiratory_cases': -1}, {'respiratory_cases': float('nan')},
                   {'respiratory_cases': 1.5}, {'respiratory_cases': True},
                   {'respiratory_cases': '10'}, {'city': None}]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    self.assess([dict(observations()[0], **change)])

    def test_invalid_metadata_or_probability_is_rejected(self):
        for threshold in [float('nan'), -0.1, 1.1]:
            self.detector.meta['threshold'] = threshold
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    MLRegionalAssessmentAdapter(self.detector)
        self.detector.meta = {}
        with self.assertRaises(ValueError):
            MLRegionalAssessmentAdapter(self.detector)
        self.detector.meta = {'threshold': 0.65}
        self.detector.window_size = 22
        with self.assertRaises(ValueError):
            MLRegionalAssessmentAdapter(self.detector)
        self.detector.window_size = 21
        for probability in [float('nan'), float('inf'), -0.1, 1.1]:
            self.detector.predict_proba = lambda history: probability
            with self.subTest(probability=probability):
                with self.assertRaises(ValueError):
                    self.assess(observations(days=21))


class TestSavedMLRegionalAdapter(unittest.TestCase):
    def test_default_adapter_matches_saved_model_without_changing_artifacts(self):
        root = Path(__file__).resolve().parent.parent
        paths = [root / p for p in ['models/ml_outbreak_model.joblib', 'models/ml_outbreak_scaler.joblib',
                                   'models/ml_outbreak_meta.json', 'reports/ml_evaluation.json']]
        before = [hashlib.sha256(p.read_bytes()).digest() for p in paths]
        adapter = MLRegionalAssessmentAdapter()
        direct = MLDetector()
        rows = observations(days=23, positives=[20]) + observations('B', days=23)
        result = adapter.assess(rows)['run']
        self.assertEqual(result['threshold'], direct.meta['threshold'])
        for hid in ['A', 'B']:
            hospital_rows = [row for row in rows if row['hospital_id'] == hid]
            for index, signal in enumerate(result['local_signals'][hid], start=20):
                history = [row['respiratory_cases'] for row in hospital_rows[:index + 1]]
                self.assertEqual(signal['predicted_probability'], direct.predict_proba(history))
                self.assertEqual(signal['anomaly_flag'], direct.predict(history))
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).digest() for p in paths])


if __name__ == '__main__':
    unittest.main()
