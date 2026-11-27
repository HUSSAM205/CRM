# Requirements Traceability Matrix

Sources: HW1 = `ST_HW1_Hussam_Aburahmah_2357138_2.pdf` (18 pages); HW2 = `ST_HW2_Hussam_Aburahmah_2357138_1.pdf` (16 pages). Page numbers are the printed numbers.

Status meanings: **PASS** = implemented and verified with the cited evidence. **PARTIAL** = partly verified, with the reason given. **N/A** = not applicable, with a justification from the HWs themselves. **NOT TESTED** = not verified.

Final update: 2026-11-27, after the independent final audit (`reports/final_audit/`). Last full run: 125 passed (`logs/testing/latest.log`). In a fresh clone of the final commit: 121 passed and 4 skipped (data-dependent).

## A. Functional requirements (HW1 1.2.1)

| ID | Src | Pg | Requirement | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| F1 | HW1 | 4 | Read user CSV, map columns, reject problem files | `src/data/ingestion.py`, `validation.py`, `app/components/upload.py` | `test_ingestion.py`, `test_validation.py`; UX tasks 1–4 | PASS |
| F2 | HW1 | 4–5 | Separate completed payments, receipts, refunds, transfers and pending before computing | `src/rules/*`, `configs/financial_rules.yaml` | `test_financial_rules.py`; ledger 49M/49M | PASS |
| F3 | HW1 | 5 | Monthly expenses; income predictions when justified; category distribution; cash flow | `src/analytics/*`; Overview and Analytics pages | `test_aggregation.py`, cross-check (0 mismatches), UX task 5 | PASS (descriptive income; the income forecast is N/A because HW1's own condition is unmet: CF-01) |
| F4 | HW1 | 5 | Label categories with a fallback policy | `merchant_category`; keyword rules; "Uncategorized" | `test_ingestion.py::test_keyword_rules_and_fallback`, `test_fallback_label_is_canonical…` | PASS |
| F5 | HW1 | 5 | Adjustable budgets with explainable advice | `src/budget/*`, Budget page | `test_budget.py`, `test_budget_editor_initial_values…`, UX task 7 | PASS |
| F6 | HW1 | 5 | Short-range estimates when history suffices; otherwise a notice | `src/models/forecasting/inference.py` | `test_model_loading.py`, UX task 8 | PASS |
| F7 | HW1 | 5 | "Candidates for review", not fraud | `anomaly_scoring.py` (LABEL), AI page | `test_full_pipeline.py`, UX task 9 | PASS |
| F8 | HW1 | 5 | Answers from valid summaries, no hallucination | `src/assistant/*` on `Summaries` | `test_assistant.py`, `test_financial_correctness.py`, UX tasks 10–11 | PASS |
| F9 | HW1 | 5 | Data deletion; no unnecessary sharing | `app/utils/session.py`, redacting logger | `test_csv_upload.py`, UX task 12 | PASS |

## B. Performance requirements (HW1 1.2.2)

| ID | Src | Pg | Requirement | Evidence | Status |
|---|---|---|---|---|---|
| P1 | HW1 | 5 | 100% of malformed CSVs end in controlled failures | Malformed-file and malformed-row cases in `test_ingestion.py`, `test_validation.py` incl. `test_huge_amounts_are_rejected_not_crashing` | PASS. Corrected in the final audit: an amount beyond the int64-cents range crashed the validator (A-01, fixed) |
| P2 | HW1 | 5 | Totals exactly equal independent references | Hand fixtures; 0 mismatches against independent `Decimal` (`financial_rules_validation.md`) | PASS |
| P3 | HW1 | 5 | Macro-F1 classification against baselines | No labeled descriptions exist (CF-02; HW1 3.1.6 makes it conditional on real labels) | N/A |
| P4 | HW1 | 5 | MAE and MASE against seasonal-naive or last-period, rolling chronological | `reports/experiments/forecasting/*` | PASS |
| P5 | HW1 | 5 | Prompt response on the final hardware | Scripted UX: mean 2.21 s per multi-step task (max 5.4 s) on the cloud container (`ux_task_results.json`); the user's laptop was not measured | PARTIAL |

## C. Constraints, design and architecture (HW1)

| ID | Src | Pg | Requirement | Evidence | Status |
|---|---|---|---|---|---|
| C1 | HW1 | 5 | CSV only; no bank or payment functions | Architecture has none (`docs/architecture.md`) | PASS |
| C2 | HW1 | 6 | Local, time-limited, no external LLM | Session-only storage, retention plus delete; no LLM; `test_csv_upload.py` | PASS |
| C3 | HW1 | 6 | Lighter benchmarks; avoid costly training on all 50M | Training on documented subsets; resource report | PASS |
| D1 | HW1 | 7–8 | Hybrid design | `docs/architecture.md` | PASS |
| A1 | HW1 | 8 | Architecture of Fig. 1; upload separate from the public data | `docs/architecture.md`; app never writes to disk (`test_app_never_writes_uploads_to_disk`) | PASS |
| A2 | HW1 | 9 | Fig. 2 flow including a **CSV report** | Overview download button (`app/utils/exports.py`) | PASS |
| W1 | HW1 | 11 | Preprocessing and financial calculations before end-to-end tests | Gate order (`docs/implementation_roadmap.md`) | PASS |
| R1–R8 | HW1 | 12 | Risk mitigations | `reports/verification/risk_and_blockers_report.md` (R3 residual: synthetic data) | PASS |

## D. Subsystem specifications (HW1 chapter 3)

| ID | Src | Pg | Requirement | Evidence | Status |
|---|---|---|---|---|---|
| S1 | HW1 | 13 | Validate timestamps, types, currency, accounts, status and totals; history window; reproducible output; no model reclassifies income | Validator; fixed mapping table; models never touch rules | PASS |
| S2 | HW1 | 13 | Python, Polars/pandas, PyArrow, scikit-learn; IF first; frozen versions | `requirements*.txt`, `environment.json` | PASS |
| S3 | HW1 | 13 | Pipeline (i)–(vii); optional prediction; calculations and predictions marked separately | Pages separate deterministic and AI sections | PASS |
| S4 | HW1 | 14 | Validation reports, summaries, score tables; versioned models; input schema | `schema.py`, registry, `artifact_verification.json` | PASS |
| S5 | HW1 | 14 | Audit, account-oriented extraction, reference calculations, train after quality criteria | Readiness gate before any training | PASS |
| S6 | HW1 | 14 | Evaluation rules | E1–E3 as specified; macro-F1 N/A (CF-02) | PASS |
| S7 | HW1 | 14 | Dashboard scope, incl. filters by account, **date** and type; no investment advice or fraud claims | Pages; date-range filter on Transactions (`test_transactions_date_filter`); unsupported "stocks" question gets the fixed reply (UX task 11) | PASS. Corrected in the final audit: the earlier PASS was wrong, because the date filter was missing (A-02, fixed) |
| S8 | HW1 | 14–15 | Streamlit; deterministic templates | `app/`, `src/assistant/` | PASS |
| S9 | HW1 | 15 | Confirm schema, choose account and currency, charts, budget screen, example question | UX tasks 1–12 | PASS |
| S10 | HW1 | 15 | Summary-table queries, session isolation, retention | `test_csv_upload.py::test_sessions_are_isolated`, retention tests | PASS |
| S11 | HW1 | 15 | Required pages and boards | 6 sections (`app/main.py`) | PASS |
| S12 | HW1 | 15 | Task-based tests with completion and errors | 12/12 (`reports/ux_tasks/ux_task_results.json`) | PASS |

## E. Dataset (HW1 chapter 4 and HW2 chapter 4)

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| DS1 | Source, license, size, hash, commit recorded | DATASET IDENTITY VERIFIED (`docs/dataset_provenance.md`) | PASS |
| DS2 | Uploads never in the training corpus | App is memory-only; training reads `data/raw` only | PASS |
| DS3 | Advertised properties verified; accounts and lengths; split counts | 27/27 integrity checks; audit; `split_metadata.json` | PASS |
| DS4 | Field treatment | Rules, D-03, feature guard | PASS |
| DS5 | Gaps respected | No salary, fraud or text classifier claims | PASS |
| DS6 | Full audit; outliers kept | `reports/data_audit/*` | PASS |
| DS7 | Preprocessing steps 1–8 | `docs/preprocessing.md`; 50M rows accounted for | PASS |
| DS8 | Leakage controls | `tests/regression/test_data_leakage.py` (L1–L11) | PASS |

## F. HW2 methodology and experiments (chapters 5–10)

| ID | Pg | Requirement | Evidence | Status |
|---|---|---|---|---|
| M5.0 | 6 | ML only for forecasting and anomalies | Architecture | PASS |
| M5.1 | 6 | Pipeline 1–7 | Gates 4–12 | PASS |
| M5.2 | 6 | Fixed mapping, transfers neutral, refunds reduce category, completed only | Tests plus ledger | PASS |
| M5.3 | 6 | Category field, keyword rules, no classifier | `ingestion.py` | PASS |
| M5.4 | 6–7 | Baselines; ETS; GBR; keep-only-if-better rule; 12-month notice | E2; selection `gbr` (validation) | PASS (finding: a post-hoc zero forecast beats GBR, see `docs/final_results.md`) |
| M5.5 | 7 | IF per account plus robust z, review candidates | E3 (per-account IF evaluated; global IF deployed, CF-16) | PASS |
| M5.6 | 7 | Median of last 3 months, editable, 80%/100% | `test_budget.py`, UX task 7 | PASS |
| M5.7 | 7 | Five intents, fixed unsupported reply | `test_assistant.py` | PASS |
| I6.1 | 8 | Tool stack, pinned versions | `requirements.txt` | PASS |
| I6.2 | 8 | Folder roles | CF-12 mapping | PASS |
| I6.3 | 8 | Batch read; subset; aggregate tables | Partitions; panels; `data/processed/` | PASS |
| I6.4 | 9 | Separate training scripts, seed 42, versioned, app loads only | `verify_artifacts.py`; ETS refused at inference | PASS |
| I6.5 | 9 | Local, per-session, retention, no raw values in logs | `test_csv_upload.py` | PASS |
| T7.1 | 10 | Eight issue resolutions | CF-02, D-03, currency rules, partitioning, status rule, injection, 12-month rule, limitations | PASS |
| E1 | 11 | Totals equal hand calculation | Tests and cross-check | PASS |
| E2 | 11 | Forecasting against baselines | `reports/experiments/forecasting/` | PASS |
| E3 | 11 | IF against z-score on injected anomalies | `reports/experiments/anomaly/` | PASS |
| E4 | 11 | Dashboard and assistant tasks | 12/12 | PASS |
| X8.2 | 11 | Split and rolling origin | `split_metadata.json`; `rolling_origin_per_month.csv` | PASS |
| X8.3 | 11 | Metrics per experiment | Results tables | PASS |
| X8.4 | 12 | 1% injection with three scenario types | `injections/labels_*.parquet` | PASS |
| X8.5 | 12 | Reproducibility | `docs/reproducibility.md`; `test_reproducibility.py` | PASS |
| V10.1 | 14 | Eight CSV validation cases | Empty, missing column, invalid timestamp, text amount, unknown currency, duplicate IDs, mixed currencies, too large: all tested | PASS |
| V10.2 | 14 | Known-answer financial tests | Fixtures | PASS |
| V10.3 | 14 | Robustness: rolling origin, short and long histories, 0.5/1/2%, seeds | Robustness tables | PASS |
| V10.4 | 14 | Assistant equals dashboard; unsupported reply | Tests plus UX tasks | PASS |
| T9 | 13 | Fill Tables 9.1 and 9.2 with measured results | `reports/final_evidence/results_tables.md` | PASS |

## Summary

69 rows. Measured tally: see `reports/verification/project_inventory.json` (`scripts/project_inventory.py`). PARTIAL: P5 (laptop responsiveness not measured). N/A: P3 (justified). No requirement was dropped silently.
