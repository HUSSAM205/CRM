# Browser Test Results

> **Master audit 2 update:** 24 tasks: tasks 23 (PersonaLedger demo shows the accepted model estimate, value equal to the engine), 24 (assistant reliability answer with account context) and 25 (emergency fund at 6 months, target equal to the engine) were added. Results: **24/24** in development and **24/24** in the fresh clone of `09c1ce4` (mean 2.43 s, max 5.91 s, 0 server tracebacks; `freshclone_final/`). Inspecting the screenshots found M-13 (truncated ranges, fixed).

Real Chromium (Playwright) driving `streamlit run app/main.py` like a user: real file-upload widget, clicks and typing. The script is `scripts/ux/ux_tasks.mjs`; expected values come from the deterministic core (`scripts/ux/ux_expected.py`), so a task passes only when the shown value equals the calculated one.

* **Development run** (2026-11-27 06:48 UTC): **21/21**, mean 2.36 s, max 5.87 s per multi-step task (cloud container). Results in `reports/ux_tasks/ux_task_results.json`.
* **Fresh clone of `0952509`:** **21/21**, mean 2.36 s, max 5.91 s, 0 tracebacks in the server log (`freshclone_final/`).
* **History:** an intermediate run in this audit gave **8/21**, caused by defect M-11 (upload crash); it was fixed and regression-tested. Earlier: 15/15 (final audit), 12/12 (build phase).

| # | Task | Verified state (not just text) | Seconds |
|---|---|---|---|
| 1 | Upload a valid CSV (bank-style signed amounts) | sidebar shows the loaded source | 3.49 |
| 2 | Reject an invalid timestamp | reason text shown | 3.11 |
| 3 | Reject an invalid amount | "Rejected rows" metric = expected count | 0.16 |
| 4 | Map missing columns (`When`→date, `Kind`→category) | "Valid rows" = 3 | 5.47 |
| 5 | View monthly totals | income, expenses and net equal independent totals | 4.15 |
| 6 | Filter a category | row count equals the groceries count | 1.80 |
| 7 | Change a budget (grid edit) | over-budget alert appears | 5.87 |
| 8 | Spending outlook | "Typical spending for…" and "NOT EFFECTIVE" banner | 0.92 |
| 9 | Unusual transactions | "Unusual transaction — review recommended." + "not a fraud finding" | 0.42 |
| 10 | Supported question | answer equals the dashboard value | 1.62 |
| 11 | Unsupported question | fixed reply | 0.87 |
| 12 | Delete uploaded data | empty state everywhere | 1.59 |
| 13 | Switch account | totals equal the second account's own data | 3.21 |
| 14 | Invalid upload keeps existing data | error shown; previous data still loaded | 3.09 |
| 16 | Reload | new empty session (nothing persisted) | 0.91 |
| 17 | Analytics tabs | "not a bank balance"; indicators without a combined score | 3.95 |
| 18 | Advisor: add a goal | surplus equals the engine; required monthly equals the engine | 3.16 |
| 19 | Advisor: what-if | labelled "Simulation, not a prediction" | 0.89 |
| 20 | Advisor: affordability | "Cannot confirm affordability" without a balance | 1.64 |
| 21 | Assistant: cash flow | answer equals the deterministic text | 1.63 |
| 22 | Settings: delete everything | goals 1 → 0; sidebar shows no data | 1.61 |

* **Task 15 (date filter):** Streamlit renders it as hidden native date inputs that a browser script cannot drive; it is verified through real widget state in `test_transactions_date_filter`.
* **Screenshots:** `reports/screenshots/ux_*.png` (one per task, at the final state) and `page_1..8_*.png` (all 8 pages with demo data). They were captured by the run, not edited.
* **Not done:** this is scripted validation, not a study with human participants.
