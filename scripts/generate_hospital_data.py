#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate reproducible synthetic daily respiratory-illness case counts
for three fictional hospitals: Tunis, Sousse, and Sfax.

Only standard library: csv, random, datetime, pathlib
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


# Fixed seed for reproducibility (same result every run)
SEED = 12345


# Hospital configuration
HOSPITALS = [
    {"hospital_id": "HOSP_TUN", "city": "Tunis"},
    {"hospital_id": "HOSP_SOU", "city": "Sousse"},
    {"hospital_id": "HOSP_SFX", "city": "Sfax"},
]


def generate_normal(start_date: date, days: int, rng: random.Random) -> list[dict]:
    """
    Generate normal scenario: stable baseline with plausible daily fluctuations.

    Baseline around 10-20 cases per hospital. Add small random variation
    (+/- 3) to keep numbers non-negative integers.
    """
    rows = []
    for h in HOSPITALS:
        baseline = rng.randint(12, 16)  # stable baseline per hospital
        current_date = start_date
        for i in range(days):
            # small daily fluctuation
            fluct = rng.randint(-3, 3)
            cases = baseline + fluct
            if cases < 0:
                cases = 0
            rows.append(
                {
                    "date": current_date.isoformat(),
                    "hospital_id": h["hospital_id"],
                    "city": h["city"],
                    "respiratory_cases": int(cases),
                    "scenario": "normal",
                }
            )
            current_date = current_date + timedelta(days=1)
    return rows


def generate_regional_outbreak(start_date: date, days: int, rng: random.Random) -> list[dict]:
    """
    Generate regional_outbreak: sustained increase across at least two hospitals
    during the final 14 days.

    Baseline similar to normal, then spike for last 14 days in Tunis and Sousse
    (at least two hospitals). Sfax stays closer to baseline to show regional effect.
    """
    rows = []
    outbreak_start_offset = days - 14  # final 14 days
    for h in HOSPITALS:
        baseline = rng.randint(12, 16)
        current_date = start_date
        for i in range(days):
            if i >= outbreak_start_offset and h["hospital_id"] in ("HOSP_TUN", "HOSP_SOU"):
                # sustained increase in final 14 days for at least two hospitals
                spike = rng.randint(15, 25)
                cases = baseline + spike
            else:
                fluct = rng.randint(-2, 2)
                cases = baseline + fluct
            if cases < 0:
                cases = 0
            rows.append(
                {
                    "date": current_date.isoformat(),
                    "hospital_id": h["hospital_id"],
                    "city": h["city"],
                    "respiratory_cases": int(cases),
                    "scenario": "regional_outbreak",
                }
            )
            current_date = current_date + timedelta(days=1)
    return rows


def generate_reporting_error(start_date: date, days: int, rng: random.Random) -> list[dict]:
    """
    Generate reporting_error: one extreme one-day spike at only one hospital,
    with the other hospitals remaining near baseline.
    """
    rows = []
    # Pick one hospital for the spike
    spike_hospital = "HOSP_TUN"  # fixed choice for reproducibility
    spike_day_offset = rng.randint(10, days - 20)  # somewhere in middle
    for h in HOSPITALS:
        baseline = rng.randint(12, 16)
        current_date = start_date
        for i in range(days):
            if h["hospital_id"] == spike_hospital and i == spike_day_offset:
                # extreme one-day spike at only one hospital
                cases = baseline + rng.randint(80, 120)  # extreme spike
            else:
                fluct = rng.randint(-2, 2)
                cases = baseline + fluct
            if cases < 0:
                cases = 0
            rows.append(
                {
                    "date": current_date.isoformat(),
                    "hospital_id": h["hospital_id"],
                    "city": h["city"],
                    "respiratory_cases": int(cases),
                    "scenario": "reporting_error",
                }
            )
            current_date = current_date + timedelta(days=1)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    """Write rows to CSV with required columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "hospital_id", "city", "respiratory_cases", "scenario"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Main function to generate all three scenarios."""
    # Reproducible RNG
    rng = random.Random(SEED)
    
    # Start date (arbitrary fixed date for reproducibility)
    start_date = date(2024, 1, 1)
    days = 90
    
    # Generate scenarios
    normal_rows = generate_normal(start_date, days, rng)
    outbreak_rows = generate_regional_outbreak(start_date, days, rng)
    error_rows = generate_reporting_error(start_date, days, rng)
    
    # Save to data/synthetic/
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"
    write_csv(data_dir / "normal.csv", normal_rows)
    write_csv(data_dir / "regional_outbreak.csv", outbreak_rows)
    write_csv(data_dir / "reporting_error.csv", error_rows)
    
    print("Generated:")
    print(f"  {data_dir / 'normal.csv'} ({len(normal_rows)} rows)")
    print(f"  {data_dir / 'regional_outbreak.csv'} ({len(outbreak_rows)} rows)")
    print(f"  {data_dir / 'reporting_error.csv'} ({len(error_rows)} rows)")


if __name__ == "__main__":
    main()
