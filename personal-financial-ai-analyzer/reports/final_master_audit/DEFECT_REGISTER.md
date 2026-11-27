# Defect Register

All defects across the project. Earlier phases are kept in full in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) (K-01..K-21 build phase, A-01..A-11 final audit). This table lists the **master audit** defects in full and the earlier ones by reference. Every code defect has a regression test that fails before its fix and passes after, unless it is marked as a report or procedure issue.

| ID | Severity | Description | Root cause | Fix | Regression test / evidence | Status |
|---|---|---|---|---|---|---|
| M-01 | P3 | Browser script used `/tmp` (fails on Windows) | hardcoded path | `os.tmpdir()` | browser run 21/21 | Fixed |
| M-02 | **P1** | File totals wrapped silently on int64 overflow: 100,000 × 999,999,999,999.99 gave −8,446,744,073,709,651,616 cents | Polars int64 sum wraps around | refuse files whose absolute total reaches 2⁶² cents (ingest and app path) | `test_file_whose_totals_would_overflow_is_refused_not_wrapped`, `test_app_upload_path_refuses_overflowing_file`, `test_large_but_safe_file_totals_stay_exact` | Fixed |
| M-03 | P3 (report) | Final-audit report stated an exact-cents bound 10× too high | writing error | corrected | — | Fixed |
| M-04 | P2 (product) | Forecasting ML shown as the forecast although it does not beat a zero baseline | HW2 rule lacks zero/median baselines | E2-QG gate; deterministic outlook; GBR labelled REJECTED (D-22) | `test_ai_page_shows_outlook_with_quality_gate_and_unusual_label`, `test_outlook_*` | Fixed |
| M-05 | P3 | Anomaly alerts lacked evidence (currency, usual amount, method, limitations); wording | minimal table | evidence columns, the required label, top 5 | AppTest; browser task 9 | Fixed |
| M-06 | P2 | `verify_artifacts.py` failed in a fresh clone without the dataset | no fallback input | demo-sample fallback | `test_artifact_verification_runs_without_derived_data` | Fixed |
| M-07 | P3 (procedure) | Fresh clones 4 and 5 used CPython 3.13 instead of the pinned 3.12 | wrong interpreter invoked by the auditor | final fresh clone with `python3.12` | `TEST_RESULTS.md` | Fixed |
| M-08 | P2 (gap) | No raw preview, encoding or delimiter handling for CSV uploads (semicolon or cp1252 exports failed) | not implemented | `detect_format` (UTF-8, BOM, cp1252, latin-1; `, ; tab \|`), preview, import summary | `test_delimiter_is_detected[4]`, `test_encodings_and_bom_are_handled`, `test_transactions_import_summary_counts` | Fixed |
| M-09 | P2 (gap) | No Advisor pillar, Settings page, analyzer insights or extended assistant intents | out of the original scope | `src/advisor`, `insights.py`, 2 pages, 8 intents | `test_advisor.py`, `test_insights.py`, `test_assistant_advisor_intents.py`, AppTests, browser tasks 17–22 | Fixed |
| M-10 | P3 | Docs whose names differed only in letter case would collide on Windows if the required uppercase names were added | naming | renamed to the uppercase names; every reference updated | inventory 167/174 (7 merged by design) | Fixed |
| M-11 | **P1** | CSV upload crashed (`NameError: detect_format`) after the preview was added | import edit missed (ruff had rewritten that line); AppTests cannot drive the file widget | import fixed | `test_upload_component_previews_detects_format_and_loads` (fails before, passes after); real-browser run 8/21 → re-run | Fixed |
| M-12 | **P1** | Uploads in TRY (or any currency outside the dataset's 6) rejected | validator reused the benchmark's currency list | any active ISO 4217 code accepted; non-currency X-codes rejected | `test_any_active_iso_currency_is_accepted_but_non_currency_codes_are_not` (fails before) | Fixed |
| M-13 | P3 | Forecast ranges truncated with "…" | long values in metric tiles | full-width text | screenshot of browser task 23 | Fixed |
| M-14 | P2 | Rule-flagged unusual transactions hidden by the ranking (Dataset C: 0% of rare categories shown) | ranking by model score only | top 5 by score + up to 5 rule hits with standard labels | `test_rule_hits_are_surfaced_with_standard_labels`; C4 before/after | Fixed |
| M-15 | P2 | "How much did I spend on unicorns?" answered with total spending | unknown category fell through to the total intent | clarification listing the categories | assistant test (fails before) | Fixed |

## Earlier defects (fixed; details in `KNOWN_ISSUES.md`)

* **K-01..K-21:** build phase. Includes K-05, an RSS of 12 GB, fixed by partitioning, and K-15, budgets shown 100× too high.
* **A-01..A-11:** final audit. Includes A-08 (P0), a broken fresh clone, and A-01 (P1), an overflow crash.
