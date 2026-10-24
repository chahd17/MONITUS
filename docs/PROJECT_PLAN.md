# MONITUS Project Plan

## Overview
This document outlines the intended modules for MONITUS and distinguishes between planned features and implemented features. The project is built incrementally, with verification at each step.

## Intended Modules

| Module | Purpose | Status |
|---|---|---|
| `frontend/` | Web interface for hospitals/authorized users to view alerts, resource requests, and coordination status. | Planned |
| `ai-service/` | AI outbreak detection engine - analyzes anonymized aggregated health signals to identify outbreak patterns and generate early warnings. | Planned |
| `hedera-service/` | Integration layer with Hedera network for decentralized logging, alerting, and coordination. | Planned |
| `contracts/` | Smart contracts (Hedera Smart Contract Service) for alert registration, resource coordination, and access control. | Planned |
| `data/` | Data schemas, anonymization utilities, and synthetic/aggregated test data (no real patient data). | Planned |
| `scripts/` | Utility scripts for setup, testing, and development workflows. | Planned |
| `tests/` | Unit, integration, and verification tests. | Planned |
| `docs/` | Project documentation (including this plan). | Partially Implemented |

## Planned Features

- **Anonymized data ingestion**: Accept only aggregated, non-identifying health signals from participating hospitals.
- **AI outbreak detection**: Train/deploy models to detect anomalies and potential outbreaks from aggregated time-series data.
- **Hedera-based alerting**: Publish outbreak alerts to a shared, immutable ledger for cross-hospital visibility.
- **Decentralized emergency response**: Enable resource requests/offers and coordination actions logged on Hedera.
- **Access control**: Role-based permissions for hospitals and authorized response entities.
- **Privacy safeguards**: Strong anonymization, no real patient data, data minimization by design.
- **Audit trail**: Immutable history of alerts and coordination actions via Hedera.

## Implemented Features

- **Project scaffolding**: Directory structure created (`frontend`, `ai-service`, `hedera-service`, `contracts`, `data`, `docs`, `scripts`, `tests`).
- **Repository initialization**: Local Git repository initialized.
- **Documentation**: `README.md` created with MONITUS concept; `docs/PROJECT_PLAN.md` created; `AGENTS.md` created with development principles.
- **Configuration**: `.gitignore` created with appropriate exclusions (Python, Node, env/secrets).
- **Synthetic hospital surveillance data (Step 2.1)**: `scripts/generate_hospital_data.py` generates reproducible synthetic data for 3 hospitals (Tunis, Sousse, Sfax) over 90 days in 3 scenarios (`normal`, `regional_outbreak`, `reporting_error`) saved as CSV in `data/synthetic/`. `tests/test_data_generation.py` validates structure and scenario characteristics.
- **Robust statistical anomaly detector - individual hospitals (Step 2.2)**: `ai_service/anomaly_detector.py` uses median and MAD with 21-day rolling window (previous days only, no leakage), flags positive anomalies with score > 3.5, handles MAD=0 with documented fallback. CLI demo on all scenarios. `tests/test_anomaly_detector.py` validates calculations and behavior. All existing tests pass.
- **Cross-hospital anomaly corroboration (Step 2.3)**: `ai_service/regional_detector.py` correlates individual anomalies by calendar date using hospital IDs, requires >= 2 distinct hospitals for regional signal (configurable), distinguishes individual vs regional, rejects duplicates, handles missing data safely, reports as "possible regional outbreak signals" not confirmed. CLI demo and `tests/test_regional_detector.py`. All tests pass.
- **Deterministic verification and false-alarm screening (Step 2.4)**: `ai_service/alert_verifier.py` classifies alerts as NORMAL/ISOLATED_ANOMALY/REGIONAL_SIGNAL_UNCONFIRMED/REGIONAL_SIGNAL_REQUIRES_REVIEW, enforces persistence (>=2 regional days in trailing 3-day window, no future leakage), keeps isolated anomalies visible, flags data-quality issues, never confirms outbreaks. CLI demo and `tests/test_alert_verifier.py`. All tests pass.

*Note: No LLM/ML training, API/frontend/Hedera/deployments yet.*
