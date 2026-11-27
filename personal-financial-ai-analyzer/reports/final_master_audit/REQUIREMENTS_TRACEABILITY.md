# Requirements Traceability (master audit)

There are two **separate** requirement sets, each with its own denominator. They are never added together.

## 1. Academic requirements (HW1 + HW2): 69 rows

The master matrix, with source PDF, page, implementation, evidence and status per row, is [`docs/requirements_traceability.md`](../../docs/requirements_traceability.md).

**Tally** (`scripts/project_inventory.py`): **67 PASS, 1 PARTIAL, 1 N/A, 0 FAIL, 0 NOT TESTED.**
* **PARTIAL: P5** (HW1 p5), responsiveness on the final hardware; the laptop was not measured.
* **N/A: P3** (HW1 p5), macro-F1 classification; HW1 3.1.6 makes it conditional on real labelled descriptions, which do not exist.

Rows updated in this audit: F6, F7, P1, S11, S12, E4, M5.4, M5.7.

### The 9 HW1 functional requirements

| ID | Requirement (HW1 p4–5) | Status | Key evidence |
|---|---|---|---|
| F1 | CSV reading, schema mapping, controlled rejection | PASS | ingestion and validation tests; M-08; browser tasks 1–4 and 14 |
| F2 | Separate completed payments, receipts, refunds, transfers, pending | PASS | rules tests; reconciliation 9,488/9,488 |
| F3 | Monthly expenses, justified income prediction, categories, cash flow | PASS (income forecast N/A by HW1's own condition, CF-01) | Overview, Analytics, insights tests |
| F4 | Category labels and fallback | PASS | keyword rules + "Uncategorized" |
| F5 | Adjustable budgets with explainable advice | PASS | budget tests; Advisor |
| F6 | Short-range forecast when history suffices, otherwise a notice | PASS (ML NOT EFFECTIVE; deterministic outlook) | `test_outlook_*` |
| F7 | Anomaly review candidates, never fraud | PASS | label test; browser task 9 |
| F8 | Constrained answers from validated summaries | PASS | assistant tests |
| F9 | Deletion and minimal sharing | PASS | retention and delete tests; browser tasks 12 and 22 |

## 2. Master-audit product requirements: 40 items (separate denominator)

| ID | Requirement (master prompt) | Implementation | Test / evidence | Status |
|---|---|---|---|---|
| R4.2 | Dataset identity vs the official source | `scripts/verify_dataset.py`, `audit/dataset_manifest.py` | `DATASET_MANIFEST.json` | PASS |
| R4.3 | Full 50M-row quality audit | `scripts/run_audit.py` | `DATA_QUALITY_REPORT.json` | PASS |
| R4.6 | Licence documented; commercial use flagged | manifest, docs | `DATASET_FORENSIC_REPORT.md` §5 | PASS (commercial use BLOCKED, legal) |
| R5.1a | Size, empty, required columns, mapping | `ingestion.py` | ingestion tests | PASS |
| R5.1b | Encoding, delimiter, preview | `detect_format`, upload preview | M-08 tests | PASS |
| R5.1c | Import summary (input, accepted, rejected, duplicates, missing, parsing, unsupported) | Transactions page | `test_transactions_import_summary_counts` | PASS |
| R5.2 | Transaction semantics incl. failed and reversed | rules + config | `test_financial_rules.py` (pending/failed/reversed) | PASS |
| R5.3 | Currency never mixed; no invented rates | `currency_rules` | `MixedCurrencyError` test | PASS (no conversion implemented) |
| R5.4 | Integer cents, rounding policy, overflow controls | validation | A-01, M-02 tests | PASS |
| R5.5 | Curated reference tests: 100% exact | fixtures | `FINANCIAL_RECONCILIATION.md` §2 | PASS |
| R5.6 | Full-dataset reconciliation | `audit/reconcile_granular.py` | 9,488/9,488 | PASS |
| R6.1 | Overview KPIs, month-over-month change, top categories, recent activity, period; not a balance | `pages/overview.py` | `test_overview_*` | PASS |
| R6.2 | Daily, weekly, monthly; statistics; filters | `insights.period_spending`, `spending_statistics` | `test_insights.py` | PASS |
| R6.3 | Income as recorded inflows, not salary | `income_analysis` | test + note | PASS |
| R6.4 | Cash flow, ratio, negative months, limitations | `cash_flow` | tests | PASS |
| R6.5 | Recurring candidates with confidence and evidence | `recurring_candidates` | rent and coffee fixture | PASS |
| R6.6 | Behaviour changes, no psychological inference | `behaviour_changes` | tests | PASS |
| R6.7 | Transparent indicators, no arbitrary score | `indicators` | `test_indicators_are_transparent…` | PASS |
| R7.3 | Baselines incl. zero | E2-QG | `MODEL_COMPARISON.csv` | PASS |
| R7.4/7.5 | Justified extra model; past-only features; no ID or balance | GBR extended | E2-QG; L1/L7 tests | PASS |
| R7.6 | Split preserved; rolling origin; MAE, MASE, RMSE, R², breakdowns | E2 + E2-QG | `FORECASTING_EXPERIMENTS.md` | PASS |
| R7.7 | Gate; fallback if no model wins | D-22 | AI-page test | PASS (ML REJECTED → fallback) |
| R7.8 | Zero-prediction investigation | E2-QG diagnostics | `FORECASTING_EXPERIMENTS.md` | PASS |
| R7.9 | Uncertainty without invented calibration | validation-calibrated interval; test coverage reported | 81.9% | PASS |
| R7.10–7.11 | Anomaly methods, injection 0.5/1/2%, 3 seeds, metrics by type | E3 | `ANOMALY_EXPERIMENTS.md` | PASS (weak results) |
| R7.12 | Required wording and evidence per alert | `anomaly_scoring` | AI-page test; browser task 9 | PASS |
| R7.13 | Model metadata, checksum, fresh-process reload | registry + `verify_artifacts` | M-06 test | PASS |
| R7.14 | Model statuses PASS/PARTIAL/REJECTED/BLOCKED | `MODEL_CARD.md` | — | PASS |
| R8.1–8.9 | Advisor | `src/advisor` | `ADVISOR_VALIDATION.md` | PASS |
| R9.1 | 12+ assistant intents | 20 intents (master audit 2) | assistant tests | PASS |
| R9.2–9.4 | Pipeline, hallucination prevention, read-only, isolation | `advisor_intents`, scope copy | `ASSISTANT_VALIDATION.md` | PASS |
| R10 | Goals, emergency fund, milestones, labels | `savings.py` | tests | PASS |
| R11 | Every page audited; controls work (incl. Settings) | 8 pages | AppTests + 21 browser tasks | PASS |
| R12 | Security and privacy tests | `test_security.py` etc. | `SECURITY_AUDIT.md` | PASS |
| R13 | Memory bounds; measured performance | guards; benchmarks | `PERFORMANCE_BENCHMARKS.md` | PARTIAL (target laptop not measured) |
| R14.1–14.4 | Unit, integration, regression and browser tests | `tests/`, `scripts/ux` | `TEST_RESULTS.md`, `BROWSER_TEST_RESULTS.md` | PASS |
| R14.5 | Fresh clone of the final commit | — | `TEST_RESULTS.md` | PASS |
| R14.6 | Windows scripts executed | `setup/run/train/audit.bat` | — | **NOT TESTED** |
| R15 | Reproducible workflow; the dataset not in git | `REPRODUCIBILITY_GUIDE.md` | fresh clones | PASS |
| R16 | Documentation set reflects the code | `docs/` (16 required names present) | — | PASS |

**Tally (40 items, counted from the table): 38 PASS (R4.6 includes a legal BLOCKED sub-item for commercial use only), 1 PARTIAL (R13), 1 NOT TESTED (R14.6), 0 FAIL.**
