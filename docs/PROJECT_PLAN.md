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

*Note: No application code, dependencies, smart contracts, or deployments have been implemented yet.*
