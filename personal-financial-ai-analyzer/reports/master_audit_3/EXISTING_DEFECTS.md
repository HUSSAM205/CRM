# Existing Defects (master audit 3, Phase 0)

Every defect here was reproduced during the inspection. Fixes and their regression tests are recorded in `DEFECT_RESOLUTION.md`.

| ID | Severity | Area | Defect | Reproduction |
|---|---|---|---|---|
| MA3-01 | High | Ingestion / data integrity | No append workflow: a second upload silently **replaced** all loaded transactions, budgets and context | Load the demo, then upload any CSV: the demo records are gone |
| MA3-02 | High | Ingestion | Generated transaction IDs included the row number, so the same transaction in two overlapping exports got different IDs. Duplicate imports across files could not be detected | Same row at line 3 in file 1 and line 1 in file 2 gives different IDs |
| MA3-03 | Medium | Assistant | "Compare this month with last month" gave the unsupported reply | `answer("Compare this month with last month", …)` |
| MA3-04 | High | Assistant (wrong answer) | "Which months had the highest spending?" was answered as the **total spending of the latest month** | The probe returned "Your total spending in 2026-07 was 9.06 USD." |
| MA3-05 | Medium | Assistant | "How much can I save?" gave the unsupported reply | probe |
| MA3-06 | Medium | Assistant | "Why was this transaction flagged?" gave the unsupported reply | probe |
| MA3-07 | Medium | Assistant | "Explain this financial indicator" and "Explain savings rate" gave the unsupported reply | probe |
| MA3-08 | High | Security | Streamlit listened on all interfaces (no `server.address`): anyone on the same network could open the app and its session data | `.streamlit/config.toml` has no address. Streamlit's default prints a "Network URL" |
| MA3-09 | Medium | Windows / launch | `run.bat` and `run_application.py` did not check `.venv`, did not detect a busy port or an already-running instance, and printed no diagnostics | static review |
| MA3-10 | Medium | Windows / setup | `setup.bat` failed without the `py` launcher; no check that an existing `.venv` uses Python 3.12; no project-file or dataset availability report | static review |
| MA3-11 | Low | Predictive | The forecast result did not state its category (validated forecast / experimental / deterministic estimate / insufficient data) | `forecast_product` output keys |
| MA3-12 | — | Anomaly / academic | **Reclassified: not a defect.** F1@k and FPR@k were already documented in `docs/ANOMALY_DETECTION.md` (final audit). They are absent only from the frozen experiment summary, which is left unchanged. Master audit 3 re-derived them (identical) and added a top-5% operating point | `reports/master_audit_3/anomaly_derived_metrics.json` |
| MA3-13 | Low | Security (defence in depth) | CSV exports did not neutralise spreadsheet formulas in text cells. Today's export has no user text, so this is not exploitable now | `app/utils/exports.py` |
| MA3-15 | Low | UI text | The rejection reason for currencies said "not one of USD, EUR, GBP, CAD, AUD, JPY", stale since M-12 accepts every ISO 4217 code | `app/utils/validation.py` |
| MA3-14 | Low | Docs | Doc names required by this audit were missing (ANALYZER_GUIDE, ADVISOR_GUIDE, ASSISTANT_GUIDE, SECURITY, PRIVACY, TEST_RESULTS, KNOWN_ISSUES, ACADEMIC_TRACEABILITY) | `ls docs` |

**Academic report-level issues.** These are carried over from `ACADEMIC_SUBMISSION_REVIEW.md` and are not code defects:
* HW1 has no bibliography;
* HW1 §4.1 has an incomplete sentence;
* P5 was not measured on the laptop;
* R3 was not done;
* HW2 Tables 9.1 and 9.2 are empty in the PDF.
