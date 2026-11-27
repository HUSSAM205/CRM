# Requirements Traceability Matrix

Sources: HW1 = `ST_HW1_Hussam_Aburahmah_2357138_2.pdf` (18 pages); HW2 = `ST_HW2_Hussam_Aburahmah_2357138_1.pdf` (16 pages). Page numbers are the printed numbers.

Status meanings: **PASS** = implemented and verified with evidence. **PARTIAL** = partly done. **NOT TESTED** = not yet implemented or verified; the planned location is given. **N/A** = not applicable, with a documented justification. **BLOCKED** = needs an unavailable resource.

Last updated: 2026-11-27, verification phase. Implementation rows are updated as each gate completes.

## A. Functional requirements (HW1 1.2.1)

| ID | Src | Pg | Requirement | Implementation | Test | Evidence | Status |
|---|---|---|---|---|---|---|---|
| F1 | HW1 | 4 | Read user CSV, map columns to the schema, reject problem files | `src/data/validation.py`; planned: `src/data/ingestion.py`, `app/components/upload.py` | `tests/unit/test_validation.py` | 18 validation tests pass | PARTIAL (validator done; CSV reader, mapping UI pending) |
| F2 | HW1 | 4–5 | Separate completed payments, receipts, refunds, transfers and pending before computing | `src/rules/transaction_mapping.py`, `transaction_status.py` | `test_financial_rules.py` | Ledger report; 9 rule tests | PASS (rules) |
| F3 | HW1 | 5 | Monthly expenses; income predictions "whenever justified"; category distribution; total cash flow | `src/analytics/financial_metrics.py` | `test_financial_rules.py`; real-data cross-check | 0 mismatches on about 1.45M groups | PARTIAL: descriptive income only; income forecast deliberately not made (CF-01) |
| F4 | HW1 | 5 | Label categories with a predefined fallback policy | Dataset `merchant_category`; "Uncategorized" fallback in `validation.py`; planned keyword rules in `src/data/preprocessing.py` | `test_missing_category_becomes_uncategorized` | test pass | PARTIAL |
| F5 | HW1 | 5 | User-adjustable budgets with explainable advice from previous months | planned: `src/budget/` | planned: `test_budget.py` | — | NOT TESTED |
| F6 | HW1 | 5 | Short-range spending estimates when history suffices; otherwise a lack-of-data notice | planned: `src/models/forecasting/` | planned: `test_forecasting.py` | Feasibility M2: 106,945 eligible series | NOT TESTED |
| F7 | HW1 | 5 | Suspicious transactions shown as "candidates for review", not fraud | planned: `src/models/anomaly/`, `app/pages/ai_predictions.py` | planned | — | NOT TESTED |
| F8 | HW1 | 5 | NL questions answered from valid summaries, without hallucination | planned: `src/assistant/` | planned: `test_assistant.py` | — | NOT TESTED |
| F9 | HW1 | 5 | Data deletion; no unnecessary sharing of raw data | planned: `app/utils/session.py` | planned: `test_csv_upload.py` | — | NOT TESTED |

## B. Performance requirements (HW1 1.2.2)

| ID | Src | Pg | Requirement | Implementation | Test | Evidence | Status |
|---|---|---|---|---|---|---|---|
| P1 | HW1 | 5 | 100% of malformed test CSVs end in controlled validation failures | `validation.py` (no exceptions on bad rows) | `test_validation.py` | 18 tests | PARTIAL (row level done; file-level cases need the CSV reader) |
| P2 | HW1 | 5 | Totals match independent reference calculations exactly, apart from explicit rounding | `financial_metrics.py` (integer cents) | `test_financial_rules.py` | Hand fixture plus real-data Decimal cross-check: 0 mismatches | PASS |
| P3 | HW1 | 5 | Classification macro-F1 against majority and rule baselines | — | — | No labeled description data (CF-02) | N/A (justified) |
| P4 | HW1 | 5 | Forecasts: MAE and MASE against seasonal-naive or last-period, rolling chronological | planned: `src/experiments/forecasting_experiment.py` | planned | — | NOT TESTED |
| P5 | HW1 | 5 | Prompt response on filtered dashboard queries | planned: app reads precomputed aggregates (HW2 6.3) | planned: UX tasks | — | NOT TESTED |

## C. Constraints, design and architecture (HW1)

| ID | Src | Pg | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|---|---|
| C1 | HW1 | 5 | CSV upload only; no bank APIs, payments or live sync | Architecture has no bank or payment code | `docs/architecture.md` (planned) | NOT TESTED |
| C2 | HW1 | 6 | Uploads local, time-limited, no external LLM without consent | planned: session store and retention; no LLM in the project | — | NOT TESTED |
| C3 | HW1 | 6 | Environmental: sampling and lighter benchmarks; avoid costly training on all 50M | Full-data audit is cheap (streaming); training on a documented subset | `resource_benchmark_report.md` | PARTIAL |
| D1 | HW1 | 7–8 | Hybrid design: deterministic totals, optional ML supplements | `src/analytics` (deterministic) separate from `src/models` | Code layout | PARTIAL |
| A1 | HW1 | 8 | Architecture: upload → validation → storage → deterministic calculations → {models, assistant, dashboard}; upload kept separate from the public dataset | planned: `docs/architecture.md` | — | NOT TESTED |
| A2 | HW1 | 9 | Flow: select account and currency → validate and deduplicate → status filter → aggregate and check sufficiency → optional ML → dashboard with explanations, warnings, **CSV report** | planned: app plus `app/utils/exports.py` | — | NOT TESTED |
| W1 | HW1 | 11 | Preprocessing and financial calculations must come before end-to-end testing | Gate order in `docs/implementation_roadmap.md` | Gates 4–5 before 13 | PASS (process) |
| R1–R8 | HW1 | 12 | Risk mitigations (history, descriptions, synthetic data, RAM, leakage, currency, privacy, time) | See `reports/verification/risk_and_blockers_report.md` | — | PARTIAL |

## D. Subsystem specifications (HW1 chapter 3)

| ID | Src | Pg | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|---|---|
| S1 | HW1 | 13 | Validate timestamps, types, currency, accounts, status and totals; choose a history window; reproducible output with confidence limitations; no model reclassifies income without a business rule | `validation.py`, `transaction_mapping.py` (fixed table); models never touch the mapping | Tests and ledger report | PARTIAL |
| S2 | HW1 | 13 | Python, pandas/Polars, PyArrow, scikit-learn; Isolation Forest first; versions frozen | `requirements.txt`, `requirements-lock.txt` | `environment.json` | PASS (stack and pins) |
| S3 | HW1 | 13 | Pipeline steps (i)–(vii); prediction optional when history is short; calculations and predictions marked separately | `src/` modules; planned UI labels | — | PARTIAL |
| S4 | HW1 | 14 | Validation reports, summary objects, model-score tables; versioned models; input schema prevents silent changes | `src/data/schema.py`; planned `artifacts/` | — | PARTIAL |
| S5 | HW1 | 14 | Audit script on the 50-row sample plus account-oriented Parquet extraction; reference calculations and unit tests; train only after quality criteria are met | `scripts/run_audit.py` (full data, beyond the sample); partition workers; this gate process | Audit reports | PASS |
| S6 | HW1 | 14 | Evaluation: hand-computed sums; macro-F1 only with real labels; rolling MAE/MASE; anomalies only on labeled or generated data | Hand fixture; planned experiments | `test_financial_rules.py` | PARTIAL |
| S7 | HW1 | 14 | Dashboard: uploads, validation errors, filters (account, date, type), charts, budgets, projections; no overselling, no investment advice, no fraud claims | planned: `app/` | — | NOT TESTED |
| S8 | HW1 | 14–15 | Streamlit; deterministic intents and templates; any later LLM read-only on aggregates | planned | — | NOT TESTED |
| S9 | HW1 | 15 | Confirm schema; choose account and currency; income/expense and category charts; budget screen shows limits and historical averages; example question answered | planned | — | NOT TESTED |
| S10 | HW1 | 15 | Dashboard queries the summary table; per-user session isolation; user-selectable retention; no outbound transfer | planned | — | NOT TESTED |
| S11 | HW1 | 15 | Pages: upload and validation, filters, category charts, budget form, forecast UI, anomaly board, query templates | planned | — | NOT TESTED |
| S12 | HW1 | 15 | Task tests: upload valid CSV; detect invalid timestamp; match monthly totals; filter category; change budget; state forecast constraint; supported and unsupported questions; track completion and errors | planned: `tests/integration`, `reports/ux_tasks` | — | NOT TESTED |

## E. Dataset (HW1 chapter 4 and HW2 chapter 4; mostly identical text)

| ID | Src | Pg | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|---|---|
| DS1 | HW1/HW2 | 16 / 3 | Record source, license, local size, hash and version commit | `scripts/download_dataset.py`, `verify_dataset.py` | `docs/dataset_provenance.md`: **DATASET IDENTITY VERIFIED** | PASS |
| DS2 | HW1/HW2 | 16 / 3 | Uploads are a separate source, never added to the training corpus | planned: app never writes to `data/` | — | NOT TESTED |
| DS3 | HW1/HW2 | 16 / 3 | Verify advertised properties (rows, columns, format, size, coverage, 6 currencies, 14 categories, 8 types, 4 statuses); measure accounts and lengths; actual split counts | `verify_dataset.py`, `run_audit.py`, `verify_methodology.py` | 27/27 integrity checks; audit; M1–M5 | PASS (split counts are recorded when splits are built) |
| DS4 | HW1/HW2 | 17 / 4 | Field treatment: ID only for dedup; account_id only for grouping and splitting; type via documented rules; amount sign verified; per-currency aggregation; category for grouping; balance_after excluded; timestamp → date, month, lags; status filter | Rules modules; ledger report | Ledger: sign verified 49M/49M | PASS (rules); features pending |
| DS5 | HW1/HW2 | 17 / 4 | Gaps: no descriptions, salary or fraud labels, demographics or budget targets | Design avoids all five | `docs/limitations.md` (planned) | PASS (design) |
| DS6 | HW1/HW2 | 17–18 / 4 | Audit: missing, invalid timestamps, duplicate IDs and rows, unknown types and statuses, bad currency, sign inconsistencies, outliers, category shares, time gaps, per-account density; a random sample is not enough; outliers investigated, not deleted | `scripts/run_audit.py` (all rows) | `reports/data_audit/*` | PASS |
| DS7 | HW1/HW2 | 18 / 4–5 | Preprocessing steps 1–8 (batches or subset; normalize and log failures; dedup by ID; separate meanings, exclude non-completed; account–currency–month aggregates; eligible accounts; past-only lags, train-only scaling; user mapping with "Uncategorized") | 2, 3, 4, 8 done in `validation.py` and rules; 1, 5, 6, 7 planned in `scripts/run_preprocessing.py`, `build_aggregates.py`, `create_splits.py` | Tests; cross-check | PARTIAL |
| DS8 | HW1/HW2 | 18 / 5 | Leakage: chronological splits; account-disjoint for generalization; dedup before split; fit on train only; no balance_after, future counts or global category totals | `docs/leakage_analysis.md`; eligibility uses train only | `methodology_feasibility.json` | PARTIAL (design verified; implementation tests pending) |

## F. HW2 methodology (chapters 5–10)

| ID | Src | Pg | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|---|---|
| M5.0 | HW2 | 6 | ML only for forecasting and anomaly ranking; totals deterministic | Module separation | — | PARTIAL |
| M5.1 | HW2 | 6 | Pipeline 1–7: ingest, validate, rules, aggregate, forecast, anomaly, dashboard | 1–3 done; 4 partial | — | PARTIAL |
| M5.2 | HW2 | 6 | Fixed type→meaning table; transfers not income or spending; refunds reduce category; completed only | `transaction_mapping.py`, `refund_rules.py`, `financial_metrics.py` | Tests; ledger | PASS |
| M5.3 | HW2 | 6 | Use merchant_category; keyword rules for user CSVs; "Uncategorized"; no text classifier | Fallback done; keyword rules planned | — | PARTIAL |
| M5.4 | HW2 | 6–7 | Target: monthly spending per account and currency. Baselines naive, seasonal naive, MA(3). ETS and GBR (lags 1–3, rolling mean, month). Keep a model only if it beats the best baseline on MAE and MASE. Fewer than 12 active months gives a notice | planned: `src/models/forecasting/` | M2 feasibility | NOT TESTED |
| M5.5 | HW2 | 7 | Isolation Forest per account on amount, hour, day of week, category and amount-to-category-median ratio; robust z (median/MAD) baseline; "review candidates" | planned: `src/models/anomaly/` | M4, M5 feasibility | NOT TESTED |
| M5.6 | HW2 | 7 | Budget = median of the last 3 completed months per category; editable; warnings at 80% and 100% | planned: `src/budget/` | — | NOT TESTED |
| M5.7 | HW2 | 7 | Fixed intents: total, category, month comparison, budget status, forecast; query on summaries; fixed unsupported reply | planned: `src/assistant/` | — | NOT TESTED |
| I6.1 | HW2 | 8 | Tools: Python 3, pandas, Polars, PyArrow, scikit-learn, statsmodels, Streamlit, Plotly, pytest, Git; versions pinned in requirements.txt | `requirements.txt`; Windows resolution check | `environment.json`, `requirements-windows-resolved.txt` | PASS |
| I6.2 | HW2 | 8 | Structure: ingest/, rules/, analytics/, models/, app/, tests/ | Mapped (CF-12) | — | PASS (mapping) |
| I6.3 | HW2 | 8 | Batch read; subset of complete-history accounts saved as a smaller Parquet; monthly aggregates as separate tables | Partitioned workers done; subset and aggregates planned | Benchmarks | PARTIAL |
| I6.4 | HW2 | 9 | Separate training scripts; seed 42; versioned saved models; the app only loads them | planned | — | NOT TESTED |
| I6.5 | HW2 | 9 | Local processing; per-user session; user-chosen retention; no raw transactions in logs; nothing sent externally | Verification logs hold aggregates only (by design); app planned | — | PARTIAL |
| T7.1 | HW2 | 10 | Eight issue resolutions (descriptions, balance_after, currencies, size, statuses, fraud labels, short histories, synthetic data) | Addressed respectively in CF-02, D-03, currency_rules, partitioning, status rule, injection plan, 12-month rule, limitations | Various | PARTIAL |
| E1 | HW2 | 11 | Totals match hand calculation exactly | `test_financial_rules.py` | 9 tests pass; real-data cross-check | PASS |
| E2 | HW2 | 11 | Forecasting models against baselines | planned | — | NOT TESTED |
| E3 | HW2 | 11 | IF against z-score on injected anomalies | planned | — | NOT TESTED |
| E4 | HW2 | 11 | Dashboard and assistant on fixed user tasks | planned | — | NOT TESTED |
| X8.2 | HW2 | 11 | Split 2024-01..2025-12 / 2026-01..04 / 2026-05..07; rolling-origin one month ahead | planned: `src/experiments/data_splitting.py` | **M1: data months equal the split union exactly** | PARTIAL (verified feasible) |
| X8.3 | HW2 | 11 | Metrics: E2 MAE, RMSE, MASE; E3 Precision@k, recall, ROC-AUC; E4 completion rate and errors | planned: `src/evaluation/` | — | NOT TESTED |
| X8.4 | HW2 | 12 | Inject 1% of test transactions in selected accounts (amount ×5–10, unusual hour, rare category) | planned: `synthetic_injection.py` | M4: 2.42 records per account → about 10k accounts for about 240 positives | NOT TESTED |
| X8.5 | HW2 | 12 | Reproducibility: seed, saved subset, fixed versions, saved settings | Pins done; others planned | — | PARTIAL |
| V10.1 | HW2 | 14 | CSV tests: empty file, missing column, invalid timestamp, text amount, unknown currency, duplicate IDs, mixed currencies, very large file | Row-level cases done; empty file, large file and mixed-currency display pending | `test_validation.py` | PARTIAL |
| V10.2 | HW2 | 14 | Known-answer files for monthly totals, categories, refunds, transfers, excluded statuses | `tests/fixtures/*` | 9 tests | PASS |
| V10.3 | HW2 | 14 | Robustness: rolling origin; short and long histories separately; injection 0.5/1/2%; different seeds | planned | — | NOT TESTED |
| V10.4 | HW2 | 14 | Assistant: supported questions equal dashboard values; unsupported gives the fixed reply | planned | — | NOT TESTED |
| T9 | HW2 | 13 | Fill Tables 9.1 and 9.2 with measured results only | planned: `reports/evaluation/` | — | NOT TESTED |

## Summary at this gate

* Requirement rows traced: **69**. HW1 R1–R8 are grouped into one row. Each functional, performance, subsystem, dataset, methodology, experiment and test requirement has its own row.
* Measured tally (`scripts/project_inventory.py`, `reports/verification/project_inventory.json`): **PASS 15 · PARTIAL 22 · NOT TESTED 31 · N/A 1 · BLOCKED 0 · FAIL 0**.
* No requirement has been dropped. The two non-implementations (income forecast CF-01, macro-F1 CF-02) are justified from the HWs' own conditions.
