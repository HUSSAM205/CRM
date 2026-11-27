# Architecture

This implements HW1's hybrid design (HW1 §1.3.3, Fig. 1): **deterministic money calculations**, with ML used only for forecasting and anomaly ranking (HW2 §5).

```
                 OFFLINE (public dataset, training)                          ONLINE (user's browser session)
 data/raw/transactions_50M.parquet (verified, read-only)          CSV upload ─► src/data/ingestion (map, parse)
        │  account-partitioned child processes (memory guard)                     │
        ▼                                                                         ▼
 src/data/validation ─► src/rules (type→meaning, status, refunds, currency) ◄── same code path
        │                                                                         │
        ▼                                                                         ▼
 src/analytics/financial_metrics (integer cents) ──► data/processed/*      src/analytics/aggregation.Summaries
        │                                                                         │
        ▼                                                                         ├─► app pages (Overview, Transactions, Analytics, Budget)
 scripts/create_splits (HW2 Table 8.1, eligibility on train only)                 ├─► src/assistant (5 fixed intents → Summaries)
        │                                                                         ├─► src/budget (median of 3 completed months)
        ▼                                                                         ├─► src/models/forecasting/inference ◄─┐
 src/experiments/{forecasting,anomaly}_experiment ──► artifacts/ (versioned) ─────┴─► src/models/anomaly/anomaly_scoring ◄┘ load only
```

## Subsystems (HW1 chapter 3)

| HW1 subsystem | Modules |
|---|---|
| 3.1 Financial data processing and AI analysis | `src/data`, `src/rules`, `src/analytics`, `src/features`, `src/models`, `src/experiments`, `src/evaluation` |
| 3.2 Dashboard and financial assistant | `app/` (Streamlit, `st.navigation`, 6 sections), `src/assistant`, `src/budget` |
| Interface between them | `Summaries` (`src/analytics/aggregation.py`) and the model registry (`artifacts/metadata/model_registry.json`) |

## Key properties

* **One rules code path.** The 50M-row pipeline and user uploads both go through `validate_transactions`, the rules modules and `financial_metrics`.
* **Exact money.** Values are integer cents, and every aggregation key includes `currency`.
* **The dashboard and the assistant share `Summaries`,** so they cannot disagree. This is tested.
* **The app never trains.** It loads registered artifacts. ETS, which would need fitting per series, is refused at inference time.
* **Privacy.** Uploads live only in `st.session_state`. There is a retention selector and a delete button. Logs redact amounts and IDs.
* **Memory safety.** All heavy offline work runs as one account partition per child process, with RSS and system-memory limits (`src/utils/resource_monitor.py`).

## Mapping to HW2 §6.2 folders

`ingest/` → `src/data/` · `rules/` → `src/rules/` · `analytics/` → `src/analytics/`, `src/budget/` · `models/` → `src/models/` · `app/` → `app/`, `src/assistant/` · `tests/` → `tests/`

## Master-list files deliberately not created (their role lives elsewhere)

| Listed file | Where the role is implemented | Why there is no separate file |
|---|---|---|
| `src/data/profiling.py` | `scripts/workers/audit_global.py`, `audit_partition.py` | Profiling must run in isolated child processes for memory safety |
| `src/features/feature_engineering.py` | `src/features/temporal_features.py`, `account_features.py` | One module per task; a façade would only re-export |
| `src/models/forecasting/forecasting_pipeline.py` | `src/experiments/forecasting_experiment.py` (training/eval), `inference.py` (serving) | Training and serving are separated by design (HW2 6.4) |
| `src/models/anomaly/anomaly_pipeline.py` | `src/experiments/anomaly_experiment.py`, `anomaly_scoring.py` | Same reason |
| `src/experiments/experiment_runner.py` | `scripts/run_full_pipeline.py` | The runner is a resumable script with guarded steps |
| `src/experiments/experiment_tracking.py` | `EXPERIMENT_REGISTRY.md`, `reports/experiments/*/summary.json`, `logs/execution/pipeline_runs.jsonl`, model registry | Tracking is file-based and versioned |
| `src/evaluation/comparison.py` | `scripts/evaluate_models.py`, `src/evaluation/error_analysis.py` | Comparison tables are produced there |
