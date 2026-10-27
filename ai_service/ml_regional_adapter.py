"""Opt-in ML local signals and regional review assessments on synthetic daily data.

No training, API/dashboard integration, or confirmed-outbreak decision. Every
observation must identify its simulation so histories and quorum cannot mix runs.
"""
from collections import deque
from datetime import date
from math import isfinite
from typing import Dict, Iterable, Optional

from ai_service.alert_verifier import AlertVerifier
from ai_service.ml_detector import MLDetector
from ai_service.regional_detector import RegionalDetector


class MLRegionalAssessmentAdapter:
    """Use the saved ML threshold with fixed two-site quorum and 2-in-3 persistence.

    ``assess`` accepts records with sim_id, hospital_id, date (YYYY-MM-DD),
    respiratory_cases (nonnegative integer), and optional city. Input order may
    vary; each hospital is sorted by date. Identical duplicates count once,
    conflicting duplicates raise ValueError. A calendar gap restarts the daily
    21-observation warm-up; missing counts are never imputed as zero/normal.

    Detector injection is for testing; production defaults to saved MLDetector.
    There is no threshold/quorum/persistence override in this adapter. These
    fixed defaults avoid the verifier's incompatible configurable-quorum edge.
    Each call is stateless and returns a separate result for each simulation.
    """

    def __init__(self, detector: Optional[MLDetector] = None):
        self.detector = detector if detector is not None else MLDetector()
        try:
            self.threshold = float(self.detector.meta['threshold'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('Saved detector must supply its validation-selected threshold') from exc
        if not isfinite(self.threshold) or not 0 <= self.threshold <= 1:
            raise ValueError('Saved threshold must be a finite probability')
        if self.detector.window_size != 21:
            raise ValueError('This daily adapter requires the saved 21-observation window')

    def assess(self, observations: Iterable[Dict]) -> Dict[str, Dict]:
        """Return local_signals, regional_reports/signals, assessments and warnings.

        local_signals includes all scored observations, with anomaly_flag meaning
        a *local* ML positive only. regional_signals contains only quorum-passing
        reports, while regional_reports also retains isolated anomalies. Neither
        a positive nor REQUIRES_REVIEW is a clinically confirmed outbreak.
        """
        groups = {}
        duplicates = {}
        for row in observations:
            sim_id, hospital_id = row.get('sim_id'), row.get('hospital_id')
            if not isinstance(sim_id, str) or not sim_id.strip():
                raise ValueError('Every observation requires an explicit nonempty sim_id')
            if not isinstance(hospital_id, str) or not hospital_id.strip():
                raise ValueError('Every observation requires a nonempty hospital_id')
            day = row.get('date')
            if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
                raise ValueError('Observation dates must use YYYY-MM-DD')
            cases = row.get('respiratory_cases')
            if isinstance(cases, bool) or not isinstance(cases, int) or cases < 0:
                raise ValueError('respiratory_cases must be a nonnegative integer count')
            city = row.get('city', '')
            if not isinstance(city, str):
                raise ValueError('city must be a string when supplied')
            normalized = {'sim_id': sim_id, 'hospital_id': hospital_id,
                          'date': day, 'respiratory_cases': cases, 'city': city}
            days = groups.setdefault(sim_id, {}).setdefault(hospital_id, {})
            if day in days:
                if days[day] != normalized:
                    raise ValueError(f'Conflicting duplicate observation for {sim_id}/{hospital_id}/{day}')
                key = (sim_id, hospital_id, day)
                duplicates[key] = duplicates.get(key, 0) + 1
            else:
                days[day] = normalized

        results = {}
        for sim_id, hospitals in sorted(groups.items()):
            local_signals = {}
            warnings = []
            for hospital_id, days in sorted(hospitals.items()):
                signals = local_signals[hospital_id] = []
                history = deque(maxlen=21)
                previous_day = None
                for day, row in sorted(days.items()):
                    day_obj = date.fromisoformat(day)
                    if previous_day is not None and (day_obj - previous_day).days != 1:
                        history.clear()
                        warnings.append({'hospital_id': hospital_id, 'date': day,
                                         'reason': 'history_reset_after_calendar_gap'})
                    previous_day = day_obj
                    duplicate_count = duplicates.get((sim_id, hospital_id, day), 0)
                    if duplicate_count:
                        warnings.append({'hospital_id': hospital_id, 'date': day,
                                         'reason': 'identical_duplicates_ignored',
                                         'ignored_records': duplicate_count})
                    history.append(row['respiratory_cases'])
                    if len(history) < 21:
                        continue
                    probability = float(self.detector.predict_proba(list(history)))
                    if not isfinite(probability) or not 0 <= probability <= 1:
                        raise ValueError('ML detector returned an invalid probability')
                    signals.append({
                        'sim_id': sim_id, 'hospital_id': hospital_id, 'date': day,
                        'city': row['city'], 'observed_cases': row['respiratory_cases'],
                        'source': 'ml', 'predicted_probability': probability,
                        'threshold': self.threshold,
                        'anomaly_flag': probability >= self.threshold,
                        'confirmed_outbreak': False,
                    })

            reports = RegionalDetector(min_supporting_hospitals=2).corroborate(local_signals)
            lookup = {(hid, signal['date']): signal
                      for hid, signals in local_signals.items() for signal in signals}
            for report in reports:
                # The legacy regional formatter inserts statistical defaults.
                # Replace them *before* verification/output: probabilities are
                # not MAD scores and the statistical >20 spike warning does not
                # apply to this source. Quorum and persistence need only flags.
                report.pop('individual_anomaly_scores')
                report['supporting_hospital_details'] = {
                    hid: dict(lookup[(hid, report['date'])])
                    for hid in report['supporting_hospitals']
                }
                report.update(source='ml', sim_id=sim_id, confirmed_outbreak=False)
            assessments = AlertVerifier(persistence_days=2, persistence_window=3).verify(
                reports, local_signals
            )
            for assessment in assessments:
                assessment.update(source='ml', sim_id=sim_id, confirmed_outbreak=False)
            results[sim_id] = {
                'sim_id': sim_id, 'source': 'ml', 'synthetic_only': True,
                'confirmed_outbreak': False, 'threshold': self.threshold,
                'local_signals': local_signals,
                'regional_reports': reports,
                'regional_signals': [report for report in reports if report['regional_signal']],
                'assessments': assessments, 'input_warnings': warnings,
            }
        return results
