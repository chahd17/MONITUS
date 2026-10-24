#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust statistical anomaly detector for individual hospitals.
Uses median and Median Absolute Deviation (MAD) with rolling window of 21 days.
Only standard library modules.
"""

from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class AnomalyDetector:
    """Robust anomaly detector using median and MAD."""
    
    # MAD scaling factor for normal distribution
    MAD_SCALING_FACTOR = 1.4826
    # Default minimum scale when MAD is 0 (documented fallback)
    MIN_SCALE_FALLBACK = 1.0
    # Default threshold for anomaly detection
    DEFAULT_THRESHOLD = 3.5
    
    def __init__(self, window_size: int = 21, threshold: float = DEFAULT_THRESHOLD):
        """
        Initialize detector.
        
        Args:
            window_size: Number of historical days to use for baseline (default 21)
            threshold: Threshold for anomaly score (default 3.5), only positive anomalies flagged
        """
        self.window_size = window_size
        self.threshold = threshold
    
    @staticmethod
    def median(values: List[float]) -> float:
        """Calculate median of a list of values."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 1:
            return float(sorted_vals[n // 2])
        else:
            return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
    
    @staticmethod
    def mad(values: List[float], med: float = None) -> Tuple[float, bool]:
        """
        Calculate Median Absolute Deviation.
        Returns (mad_value, used_fallback) where used_fallback indicates if MAD was 0.
        """
        if not values:
            return 0.0, False
        if med is None:
            med = AnomalyDetector.median(values)
        # Calculate absolute deviations from median
        deviations = [abs(x - med) for x in values]
        mad_val = AnomalyDetector.median(deviations)
        used_fallback = False
        if mad_val == 0:
            used_fallback = True
            # Use minimum scale fallback when MAD is 0
            mad_val = AnomalyDetector.MIN_SCALE_FALLBACK
        return mad_val, used_fallback
    
    def detect_anomalies_for_hospital(self, observations: List[Dict]) -> List[Dict]:
        """
        Detect anomalies for a single hospital.
        observations must be sorted by date.
        For each day after initial window_size days, use only PREVIOUS window_size days.
        Never includes current day or future observations.
        """
        results = []
        if len(observations) < self.window_size + 1:
            # Not enough history
            return results
        
        for i in range(self.window_size, len(observations)):
            current = observations[i]
            current_cases = float(current['respiratory_cases'])
            current_date = current['date']
            
            # Get PREVIOUS window_size days only (no current, no future)
            history = observations[i - self.window_size:i]
            history_values = [float(h['respiratory_cases']) for h in history]
            
            # Calculate median and MAD of historical window
            hist_median = self.median(history_values)
            hist_mad, mad_fallback = self.mad(history_values, hist_median)
            
            # Calculate robust anomaly score
            scale = self.MAD_SCALING_FACTOR * hist_mad
            if scale == 0:
                scale = self.MIN_SCALE_FALLBACK
            
            score = (current_cases - hist_median) / scale if scale > 0 else 0.0
            
            # Flag positive anomalies above threshold only (do not flag low values)
            is_anomaly = False
            if score > self.threshold:
                is_anomaly = True
            
            results.append({
                'date': current_date,
                'hospital_id': current['hospital_id'],
                'city': current.get('city', ''),
                'observed_cases': int(current_cases),
                'baseline_median': round(hist_median, 2),
                'mad': round(hist_mad, 2),
                'mad_fallback_used': mad_fallback,
                'anomaly_score': round(score, 4),
                'anomaly_flag': is_anomaly
            })
        
        return results
    
    def load_csv(self, csv_path: Path) -> Dict[str, List[Dict]]:
        """
        Load CSV and group by hospital_id, sorted by date.
        """
        hospitals_data = {}
        with csv_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hid = row['hospital_id']
                if hid not in hospitals_data:
                    hospitals_data[hid] = []
                hospitals_data[hid].append(row)
        
        # Sort each hospital's data by date
        for hid in hospitals_data:
            hospitals_data[hid].sort(key=lambda x: x['date'])
        
        return hospitals_data
    
    def analyze_file(self, csv_path: Path) -> Dict[str, List[Dict]]:
        """
        Analyze all hospitals in a CSV file.
        Returns dict mapping hospital_id to list of anomaly results.
        """
        hospitals_data = self.load_csv(csv_path)
        all_results = {}
        for hid, observations in hospitals_data.items():
            results = self.detect_anomalies_for_hospital(observations)
            all_results[hid] = results
        return all_results


def print_summary(results_by_hospital: Dict[str, List[Dict]], scenario_name: str):
    """Print readable summary for each hospital."""
    print(f"\n{'=' * 70}")
    print(f"Scenario: {scenario_name}")
    print(f"{'=' * 70}")
    
    for hid in sorted(results_by_hospital.keys()):
        results = results_by_hospital[hid]
        city = results[0]['city'] if results else hid
        print(f"\n{city} ({hid}):")
        print(f"  Total days analyzed: {len(results)} (after 21-day history)")
        anomaly_days = [r for r in results if r['anomaly_flag']]
        print(f"  Anomalous days (score > 3.5): {len(anomaly_days)}")
        if anomaly_days:
            print(f"  Anomaly details:")
            for ad in anomaly_days:
                print(f"    {ad['date']}: cases={ad['observed_cases']}, "
                      f"median={ad['baseline_median']}, MAD={ad['mad']}, "
                      f"score={ad['anomaly_score']:.4f}")
        else:
            print(f"  No anomalies detected above threshold.")


def main():
    """CLI demonstration on all three scenarios."""
    detector = AnomalyDetector(window_size=21, threshold=3.5)
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"
    
    scenarios = ["normal.csv", "regional_outbreak.csv", "reporting_error.csv"]
    
    for scenario_file in scenarios:
        csv_path = data_dir / scenario_file
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            continue
        scenario_name = scenario_file.replace(".csv", "")
        results = detector.analyze_file(csv_path)
        print_summary(results, scenario_name)
    
    print(f"\n{'=' * 70}")
    print("Note: Individual hospital anomalies detected. No regional corroboration performed.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
