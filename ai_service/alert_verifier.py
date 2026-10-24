#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic verification and false-alarm screening for alerts.
Takes regional detection reports and produces assessment status with evidence.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Set


class AlertVerifier:
    """Deterministic verifier for anomaly alerts."""
    
    STATUSES = [
        "NORMAL",
        "ISOLATED_ANOMALY",
        "REGIONAL_SIGNAL_UNCONFIRMED",
        "REGIONAL_SIGNAL_REQUIRES_REVIEW"
    ]
    
    def __init__(self, persistence_days: int = 2, persistence_window: int = 3):
        """
        Initialize verifier.
        
        Args:
            persistence_days: Minimum regional signal days needed in window
            persistence_window: Trailing window size in calendar days
        """
        self.persistence_days = persistence_days
        self.persistence_window = persistence_window
    
    def verify(self, regional_reports: List[Dict], 
               individual_results_by_hospital: Dict[str, List[Dict]] = None) -> List[Dict]:
        """
        Verify regional reports with deterministic rules.
        Uses only evidence on or before assessed date (no future leakage).
        """
        assessments = []
        
        # Build lookup of regional signals by date
        regional_by_date = {}
        for report in regional_reports:
            regional_by_date[report['date']] = report
        
        # Sort dates
        all_dates = sorted(regional_by_date.keys())
        
        for idx, report_date in enumerate(all_dates):
            report = regional_by_date[report_date]
            report_date_obj = date.fromisoformat(report_date)
            
            checks_passed = []
            checks_failed = []
            data_quality_warnings = []
            evidence_dates = [report_date]
            
            num_supporting = report['num_supporting_sites']
            supporting_hospitals = report['supporting_hospitals']
            
            # Check for duplicates/missing observations
            if individual_results_by_hospital:
                # Check for duplicates
                for hid in supporting_hospitals:
                    if hid in individual_results_by_hospital:
                        hosp_results = individual_results_by_hospital[hid]
                        dates_seen = []
                        for r in hosp_results:
                            if r['date'] == report_date:
                                dates_seen.append(r)
                        if len(dates_seen) > 1:
                            data_quality_warnings.append(f"Duplicate records for {hid} on {report_date}")
                            checks_failed.append("no_duplicates")
                        else:
                            checks_passed.append("no_duplicates")
                    else:
                        data_quality_warnings.append(f"Missing observations for {hid} referenced in report")
                        checks_failed.append("observations_present")
            
            if num_supporting == 0:
                status = "NORMAL"
                explanation = "No supporting hospitals with anomalies."
            elif num_supporting == 1:
                status = "ISOLATED_ANOMALY"
                explanation = (f"Single-site isolated anomaly at {supporting_hospitals[0]} on {report_date}. "
                              f"Not enough for regional corroboration. Must remain visible for local investigation. "
                              f"This is NOT a confirmed outbreak.")
                # Check for extremely unusual isolated spikes
                details = report.get('supporting_hospital_details', {})
                for hid, det in details.items():
                    score = det.get('anomaly_score', 0)
                    if score > 20:  # Extremely unusual
                        data_quality_warnings.append(
                            f"Extremely unusual isolated spike at {hid} (score={score:.2f}) - "
                            f"requires local investigation but not automatically assumed as error"
                        )
            elif num_supporting >= 2:
                # Multi-site regional signal
                # Check persistence in trailing window (on or before this date, no future)
                trailing_start = report_date_obj - timedelta(days=self.persistence_window - 1)
                regional_signal_dates_in_window = []
                for check_date in all_dates:
                    check_date_obj = date.fromisoformat(check_date)
                    if trailing_start <= check_date_obj <= report_date_obj:
                        if regional_by_date[check_date].get('regional_signal', False):
                            regional_signal_dates_in_window.append(check_date)
                
                if len(regional_signal_dates_in_window) >= self.persistence_days:
                    status = "REGIONAL_SIGNAL_REQUIRES_REVIEW"
                    explanation = (f"Regional signal involving {num_supporting} hospitals on {report_date}, "
                                  f"with persistence: {len(regional_signal_dates_in_window)} regional-signal days "
                                  f"in trailing {self.persistence_window}-day window. Requires review. "
                                  f"NOT a confirmed outbreak.")
                    checks_passed.append("persistence_check")
                    evidence_dates = sorted(regional_signal_dates_in_window)
                else:
                    status = "REGIONAL_SIGNAL_UNCONFIRMED"
                    explanation = (f"Regional signal involving {num_supporting} hospitals on {report_date} "
                                  f"(same day), but persistence check not met: only "
                                  f"{len(regional_signal_dates_in_window)} regional-signal days in trailing "
                                  f"{self.persistence_window}-day window (need >= {self.persistence_days}). "
                                  f"Signal unconfirmed. NOT a confirmed outbreak.")
                    checks_failed.append("persistence_check")
                    evidence_dates = sorted(regional_signal_dates_in_window)
            else:
                status = "NORMAL"
                explanation = "No anomalies."
            
            assessments.append({
                'date': report_date,
                'status': status,
                'supporting_hospitals': supporting_hospitals,
                'num_supporting_sites': num_supporting,
                'explanation': explanation,
                'evidence_dates': evidence_dates,
                'checks_passed': checks_passed,
                'checks_failed': checks_failed,
                'data_quality_warnings': data_quality_warnings
            })
        
        return assessments
    
    def analyze_scenario(self, csv_path: Path, detector=None, regional_detector=None) -> List[Dict]:
        """Analyze a full scenario."""
        from ai_service.anomaly_detector import AnomalyDetector
        from ai_service.regional_detector import RegionalDetector
        
        if detector is None:
            detector = AnomalyDetector(window_size=21, threshold=3.5)
        if regional_detector is None:
            regional_detector = RegionalDetector(min_supporting_hospitals=2)
        
        individual_results = detector.analyze_file(csv_path)
        regional_reports = regional_detector.corroborate(individual_results)
        assessments = self.verify(regional_reports, individual_results)
        return assessments


def print_verification_summary(assessments: List[Dict], scenario_name: str):
    """Print readable summary."""
    print(f"\n{'=' * 70}")
    print(f"Alert Verification - Scenario: {scenario_name}")
    print(f"{'=' * 70}")
    
    for a in assessments:
        print(f"\n{a['date']}: {a['status']}")
        print(f"  Supporting sites: {a['num_supporting_sites']} - {a['supporting_hospitals']}")
        print(f"  {a['explanation']}")
        if a['data_quality_warnings']:
            print(f"  Data quality warnings:")
            for w in a['data_quality_warnings']:
                print(f"    - {w}")


def main():
    """CLI demo for all three scenarios."""
    verifier = AlertVerifier(persistence_days=2, persistence_window=3)
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"
    
    scenarios = ["normal.csv", "regional_outbreak.csv", "reporting_error.csv"]
    
    for scenario_file in scenarios:
        csv_path = data_dir / scenario_file
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            continue
        scenario_name = scenario_file.replace(".csv", "")
        assessments = verifier.analyze_scenario(csv_path)
        print_verification_summary(assessments, scenario_name)
    
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()
