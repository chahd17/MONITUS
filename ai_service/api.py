#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MONITUS minimal read-only FastAPI for existing disease-surveillance engine.
Uses existing ai_service modules without duplicating logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from ai_service.anomaly_detector import AnomalyDetector
from ai_service.regional_detector import RegionalDetector
from ai_service.alert_verifier import AlertVerifier


app = FastAPI(
    title="MONITUS Surveillance API",
    description="Read-only API for synthetic disease surveillance data using existing detection engines",
    version="1.0.0"
)

PERMITTED_SCENARIOS = ["normal", "regional_outbreak", "reporting_error"]
DATA_DIR = Path(__file__).parent.parent / "data" / "synthetic"


def _get_scenario_path(scenario: str) -> Path:
    if scenario not in PERMITTED_SCENARIOS:
        raise HTTPException(status_code=422, detail=f"Invalid scenario. Permitted: {PERMITTED_SCENARIOS}")
    csv_path = DATA_DIR / f"{scenario}.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario data not found: {scenario}")
    return csv_path


def _analyze(scenario: str):
    csv_path = _get_scenario_path(scenario)
    detector = AnomalyDetector(window_size=21, threshold=3.5)
    regional_detector = RegionalDetector(min_supporting_hospitals=2)
    verifier = AlertVerifier(persistence_days=2, persistence_window=3)
    
    individual_results = detector.analyze_file(csv_path)
    regional_reports = regional_detector.corroborate(individual_results)
    assessments = verifier.verify(regional_reports, individual_results)
    
    return individual_results, regional_reports, assessments


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "monitus-surveillance-api",
        "synthetic_only": True,
        "confirmed_outbreak": False,
        "note": "No confirmed disease outbreak claims"
    }


@app.get("/api/v1/scenarios")
def scenarios():
    return {
        "permitted_scenarios": PERMITTED_SCENARIOS,
        "synthetic_only": True
    }


@app.get("/api/v1/surveillance/summary")
def surveillance_summary(scenario: str = Query(..., description="Scenario name")):
    individual_results, regional_reports, assessments = _analyze(scenario)
    
    hospital_summary = []
    for hid in ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"]:
        results = individual_results.get(hid, [])
        anomaly_count = sum(1 for r in results if r.get('anomaly_flag', False))
        city = results[0]['city'] if results else hid
        hospital_summary.append({
            "hospital_id": hid,
            "city": city,
            "anomaly_count": anomaly_count,
            "synthetic": True
        })
    
    regional_signals = [r for r in regional_reports if r.get('regional_signal', False)]
    
    return {
        "scenario": scenario,
        "synthetic_only": True,
        "confirmed_outbreak": False,
        "hospitals": hospital_summary,
        "regional_signal_dates": [r['date'] for r in regional_signals],
        "regional_signal_count": len(regional_signals),
        "verification_statuses": [
            {"date": a['date'], "status": a['status'], "supporting_hospitals": a['supporting_hospitals']}
            for a in assessments
        ]
    }


@app.get("/api/v1/surveillance/alerts")
def surveillance_alerts(scenario: str = Query(..., description="Scenario name")):
    individual_results, regional_reports, assessments = _analyze(scenario)
    
    alerts = []
    for a in assessments:
        alerts.append({
            "date": a['date'],
            "status": a['status'],
            "supporting_hospitals": a['supporting_hospitals'],
            "num_supporting_sites": a['num_supporting_sites'],
            "explanation": a['explanation'],
            "evidence_dates": a['evidence_dates'],
            "checks_passed": a['checks_passed'],
            "checks_failed": a['checks_failed'],
            "data_quality_warnings": a['data_quality_warnings'],
            "synthetic": True,
            "confirmed_outbreak": False
        })
    
    return {
        "scenario": scenario,
        "synthetic_only": True,
        "confirmed_outbreak": False,
        "alerts": alerts,
        "regional_signal_dates": [r['date'] for r in regional_reports if r.get('regional_signal', False)]
    }


@app.get("/api/v1/surveillance/hospitals")
def surveillance_hospitals(scenario: str = Query(..., description="Scenario name")):
    individual_results, regional_reports, assessments = _analyze(scenario)
    
    hospitals = []
    for hid in ["HOSP_TUN", "HOSP_SOU", "HOSP_SFX"]:
        results = individual_results.get(hid, [])
        anomalies = [r for r in results if r.get('anomaly_flag', False)]
        city = results[0]['city'] if results else hid
        hospitals.append({
            "hospital_id": hid,
            "city": city,
            "synthetic": True,
            "anomaly_count": len(anomalies),
            "anomalies": [
                {
                    "date": a['date'],
                    "observed_cases": a['observed_cases'],
                    "baseline_median": a['baseline_median'],
                    "mad": a['mad'],
                    "anomaly_score": a['anomaly_score'],
                    "anomaly_flag": a['anomaly_flag']
                }
                for a in anomalies
            ]
        })
    
    return {
        "scenario": scenario,
        "synthetic_only": True,
        "confirmed_outbreak": False,
        "hospitals": hospitals
    }
