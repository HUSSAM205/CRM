# Application Audit (Streamlit)

Methods:
* Headless AppTest (`tests/integration/test_dashboard.py`, `test_csv_upload.py`).
* A real Chromium browser driven by Playwright (`scripts/ux/ux_tasks.mjs`, run against `streamlit run app/main.py`).
* Code review.

Results are in `reports/ux_tasks/ux_task_results.json` (run 2026-11-27T05:17Z): **15/15 tasks completed, mean 2.40 s, max 5.88 s per multi-step task**. Screenshots are in `reports/screenshots/ux_*.png` and `page_1..6_*.png`.

| # | Real-browser task | Result |
|---|---|---|
| 1 | Upload a bank-style signed CSV, confirm "completed", load | PASS |
| 2–3 | Invalid timestamp and invalid amount rejected with plain-text reasons; rejected count equals the expected value | PASS |
| 4 | Map unknown columns (`When`→date, `Kind`→category) | PASS |
| 5 | Monthly KPIs equal independently computed totals | PASS |
| 6 | Category filter row count | PASS |
| 7 | Edit a budget in the grid → over-budget alert | PASS (after harness fix A-10) |
| 8–9 | Forecast and anomaly "review candidate" labeling | PASS |
| 10–11 | Supported question equals the dashboard; unsupported question gets the fixed reply | PASS |
| 12 | Delete my data → empty state everywhere | PASS |
| 13 | Switch account → that account's own totals (isolation) | PASS |
| 14 | Fully invalid upload → message; previous data kept | PASS |
| 16 | Reload → new session; nothing persisted | PASS |
| (15) | Date-range filter. Streamlit 1.67 renders hidden native date inputs that the script cannot drive, so it is verified through the real widget state instead (`test_transactions_date_filter`) | PASS (AppTest, not browser) |

## Defects found and fixed in this audit

* **A-02 (P2):** the HW1 S7 date filter was missing. Added.
* **A-03 (P2):** user-controlled strings (file name, categories, questions) were rendered as Markdown. Now escaped, and assistant answers render as plain text.
* **A-04 (P3):** Streamlit telemetry was on by default and tracebacks were shown in the browser. Fixed in `.streamlit/config.toml`.
* **A-06 (P3):** deprecated `use_container_width` replaced.
* **A-10 (test harness):** a flaky budget-edit step. The cause was an immediate Enter before the grid editor registered the typed text. The app was not at fault, which a standalone reproduction confirmed.

## Six sections present

Overview, Transactions, Analytics, AI predictions, Budget, Financial assistant (`app/main.py`; every page renders without an exception in AppTest, with and without data).

## Limitations

* No human-participant study: the UX validation is scripted.
* The accessibility review was partial: plain-text reasons and labeled widgets, but no screen-reader run.
* The UI is English only. Arabic questions get the unsupported reply (`assistant_probe.txt`).
