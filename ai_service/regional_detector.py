#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-hospital anomaly corroboration (regional detector).
Combines individual hospital anomaly results by calendar date.
Requires at least 2 distinct hospitals with positive anomaly flags on the same date.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

from ai_service.anomaly_detector import AnomalyDetector


class RegionalDetector:
    """Regional corroboration of individual hospital anomalies."""
    
    DEFAULT_MIN_SUPPORTING = 2
    
    def __init__(self, min_supporting_hospitals: int = DEFAULT_MIN_SUPPORTING):
        self.min_supporting_hospitals = min_supporting_hospitals
    
    def corroborate(self, individual_results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Corroborate individual anomalies across hospitals by calendar date.
        individual_results: dict mapping hospital_id -> list of anomaly result dicts
        Uses hospital IDs (not row positions). Counts distinct hospitals per date.
        Rejects duplicates by (date, hospital_id).
        """
        # Build map: date -> list of supporting hospital results
        date_to_hospitals = {}
        
        for hid, results in individual_results.items():
            seen_pairs = set()  # track (date, hid) to reject duplicates
            for r in results:
                date_str = r['date']
                pair = (date_str, hid)
                if pair in seen_pairs:
                    continue  # reject duplicate
                seen_pairs.add(pair)
                
                if r.get('anomaly_flag', False):
                    if date_str not in date_to_hospitals:
                        date_to_hospitals[date_str] = []
                    date_to_hospitals[date_str].append({
                        'hospital_id': hid,
                        'city': r.get('city', ''),
                        'anomaly_score': r.get('anomaly_score', 0.0),
                        'observed_cases': r.get('observed_cases', 0),
                        'baseline_median': r.get('baseline_median', 0.0),
                        'mad': r.get('mad', 0.0)
                    })
        
        # Build regional report
        regional_reports = []
        all_dates = sorted(date_to_hospitals.keys())
        
        for date_str in all_dates:
            hospital_list = date_to_hospitals[date_str]
            # Get distinct hospitals (should already be distinct by construction)
            distinct_hospitals = {}
            for h in hospital_list:
                hid = h['hospital_id']
                if hid not in distinct_hospitals:
                    distinct_hospitals[hid] = h
                # If duplicate somehow, keep first occurrence
            supporting_hospitals = list(distinct_hospitals.keys())
            num_supporting = len(supporting_hospitals)
            
            regional_signal = num_supporting >= self.min_supporting_hospitals
            
            if regional_signal:
                reason = f"Possible regional outbreak signal: {num_supporting} distinct hospitals show positive anomalies on {date_str} (>= {self.min_supporting_hospitals} required). This is NOT a confirmed outbreak."
            elif num_supporting == 1:
                reason = f"Individual-hospital anomaly only: 1 hospital ({supporting_hospitals[0]}) shows positive anomaly on {date_str}. Not enough for regional corroboration."
            else:
                reason = f"Insufficient supporting hospitals ({num_supporting}) for regional signal."
            
            regional_reports.append({
                'date': date_str,
                'supporting_hospitals': sorted(supporting_hospitals),
                'supporting_hospital_details': {hid: distinct_hospitals[hid] for hid in sorted(distinct_hospitals.keys())},
                'num_supporting_sites': num_supporting,
                'regional_signal': regional_signal,
                'explanatory_reason': reason,
                'individual_anomaly_scores': {hid: distinct_hospitals[hid]['anomaly_score'] for hid in sorted(distinct_hospitals.keys())}
            })
        
        return regional_reports
    
    def analyze_file(self, csv_path: Path, detector: AnomalyDetector = None) -> List[Dict]:
        """Analyze a CSV file for regional signals."""
        if detector is None:
            detector = AnomalyDetector(window_size=21, threshold=3.5)
        individual_results = detector.analyze_file(csv_path)
        return self.corroborate(individual_results)


def print_regional_summary(regional_reports: List[Dict], scenario_name: str):
    """Print readable summary of regional signals."""
    print(f"\n{'=' * 70}")
    print(f"Regional Corroboration - Scenario: {scenario_name}")
    print(f"{'=' * 70}")
    
    regional_signals = [r for r in regional_reports if r['regional_signal']]
    individual_only = [r for r in regional_reports if not r['regional_signal'] and r['num_supporting_sites'] >= 1]
    
    print(f"Regional signal days (>= 2 hospitals): {len(regional_signals)}")
    if regional_signals:
        print(f"Regional signal dates:")
        for rs in regional_signals:
            print(f"  {rs['date']}: {rs['supporting_hospitals']} (scores: {rs['individual_anomaly_scores']})")
    
    print(f"\nIndividual-hospital anomalies only (1 site): {len(individual_only)}")
    if individual_only and len(individual_only) <= 5:
        for io in individual_only:
            print(f"  {io['date']}: {io['supporting_hospitals']} (score: {io['individual_anomaly_scores']})")
    elif individual_only:
        print(f"  (showing first 5 of {len(individual_only)})")
        for io in individual_only[:5]:
            print(f"  {io['date']}: {io['supporting_hospitals']} (score: {io['individual_anomaly_scores']})")
    
    print(f"\nNote: Results are 'possible regional outbreak signals', NOT confirmed outbreaks.")


def main():
    """CLI demo for all three scenarios."""
    detector = AnomalyDetector(window_size=21, threshold=3.5)
    regional = RegionalDetector(min_supporting_hospitals=2)
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"
    
    scenarios = ["normal.csv", "regional_outbreak.csv", "reporting_error.csv"]
    
    for scenario_file in scenarios:
        csv_path = data_dir / scenario_file
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            continue
        scenario_name = scenario_file.replace(".csv", "")
        regional_reports = regional.analyze_file(csv_path, detector)
        print_regional_summary(regional_reports, scenario_name)
    
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()
