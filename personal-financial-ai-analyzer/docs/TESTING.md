# Testing Report

Run with `python -m pytest` (or `test.bat`). The test files are:

| Level | Files | What they prove |
|---|---|---|
| Unit | `tests/unit/test_validation.py`, `test_ingestion.py` | every malformed file or row fails in a controlled way: encoding, delimiter, overflow (A-01, M-02), currencies (M-12), duplicates, precision |
| Unit | `test_financial_rules.py`, `test_aggregation.py` | hand-calculated totals, refunds, transfers, fees, status filtering |
| Unit | `test_insights.py`, `test_advisor.py`, `test_assistant.py`, `test_assistant_advisor_intents.py` | Analyzer, Advisor and Assistant known answers, account isolation, read-only behaviour |
| Unit | `test_budget.py`, `test_forecasting.py`, `test_anomaly.py` | HW2 methods |
| Unit | `test_preprocessing.py` | the 50M-row pipeline steps |
| Unit | `test_controlled_synthetic.py` | Dataset C determinism, exact financials, rule-hit surfacing |
| Unit | `test_merge.py` (master audit 3) | append/import: overlapping exports, re-import, cross-account IDs, combined range; position-independent generated IDs |
| Unit | `test_assistant_ma3.py` (master audit 3) | relative month comparison, highest months, savings capacity, flag explanations, indicator explanations, clarification, refusals |
| Integration | `test_launcher.py` (master audit 3) | local-only binding (not reachable through the network address), no duplicate server, busy-port message |
| Integration | `tests/integration/test_dashboard.py` | all 8 pages render; page values equal the engine; goal editing; context display |
| Integration | `test_csv_upload.py` | upload path, retention, deletion, isolation, upload-component preview |
| Integration | `test_model_loading.py` | saved models load; product routing (D-24); feature parity with E2-B; artifact verification without data |
| Integration | `test_full_pipeline.py` | CSV → analytics → models → assistant |
| Regression | `tests/regression/test_data_leakage.py` | L1–L11 |
| Regression | `test_reproducibility.py` | saved models reproduce recorded predictions |
| Regression | `test_financial_correctness.py` | known-answer fixture |
| Regression | `test_repository_completeness.py` | required files tracked; no datasets tracked |
| Regression | `test_security.py` | deserialization, injection, network, error disclosure, redaction |
| Browser | `scripts/ux/ux_tasks.mjs` (Playwright, 29 tasks) | real user workflows with value checks; screenshots in `reports/screenshots/` |

Results and counts: `reports/master_audit_3/FINAL_TEST_RESULTS.md`. Every defect in `KNOWN_ISSUES.md` has a regression test or re-run evidence.
