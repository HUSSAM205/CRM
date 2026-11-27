# Implementation Inventory (master audit 3, Phase 0)

Status meanings:
* **Functional**: implemented, with tests.
* **Partial**: implemented, with a gap described here.
* **Broken**: gives wrong output.
* **Missing**: not implemented.
* **Unverified**: no evidence yet.

These statuses are from the inspection **before** the fixes in this audit. Final statuses: `FINAL_MASTER_AUDIT.md`.

| Area | Component | Code | Status at baseline | Notes |
|---|---|---|---|---|
| Ingestion | CSV read, encoding and delimiter detection, size and row limits | `src/data/ingestion.py` | Functional | |
| Ingestion | Column mapping, sign-to-type, keyword categories | `src/data/ingestion.py`, `app/components/upload.py` | Functional | |
| Ingestion | Row validation, ISO 4217 currencies, duplicates within a file, overflow guard | `src/data/validation.py`, `schema.py` | Functional | |
| Ingestion | **Append a second file to loaded data** | — | **Missing** | Every upload replaced the session data (`session.set_data`) with no confirmation |
| Ingestion | **Duplicate-import prevention across files** | — | **Missing** | Generated IDs depended on the row position, so overlapping exports would not match |
| Analyzer | Daily, weekly and monthly spending; category; income; cash flow; recurring; trends; indicators | `src/analytics/*` | Functional | |
| Advisor | Profile, essential/non-essential, surplus, goals (create/edit, milestones, status), emergency fund (user-chosen coverage), scenarios, affordability, recommendations | `src/advisor/*`, `app/pages/financial_advisor.py` | Functional | The balance is never inferred; affordability is never confirmed when facts are unknown |
| Predictive | Product forecast routing (E2-B in domain, deterministic median otherwise) | `src/models/forecasting/inference.py` | Partial | No explicit category label (validated / experimental / deterministic / insufficient data) |
| Anomaly | Review candidates: global IF plus rules, labels, not-fraud note | `src/models/anomaly/anomaly_scoring.py` | Functional | E3 reports precision, recall and AUC; **F1 and FPR are not reported** |
| Assistant | 27 deterministic intents, account and currency scoping, refusals | `src/assistant/*` | **Partial / Broken** | See `EXISTING_DEFECTS.md` MA3-03..07 (one wrong answer, four unsupported questions) |
| UI | 8 pages, navigation, empty states | `app/` | Functional | |
| Security | Markdown escaping, plain-text assistant, no disk writes, redacting logger, telemetry off | `app/utils/formatting.py`, `.streamlit/config.toml` | **Partial** | The server listens on all network interfaces (no `server.address`) |
| Windows | `setup.bat`, `run.bat`, `test.bat`, `train.bat`, `audit.bat`, `benchmark.bat` and `.ps1` twins | root | Partial | No `.venv` check in `run.bat`, no port or duplicate-instance check, setup needs the `py` launcher. NOT TESTED on Windows |
| Docs | 25+ docs, academic review | `docs/`, `reports/` | Partial | Some file names requested by this audit are missing; HW1 bibliography gap (report level) |
| Tests | 196 tests, 24 browser tasks, fresh clone | `tests/`, `scripts/ux/` | Functional | |
