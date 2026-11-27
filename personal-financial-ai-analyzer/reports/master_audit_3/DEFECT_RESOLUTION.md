# Defect Resolution (master audit 3)

Each defect was reproduced first (`EXISTING_DEFECTS.md`), then fixed and covered by a regression test that exercises the failing behaviour.

| ID | Fix | Files | Regression test | Status |
|---|---|---|---|---|
| MA3-01 | Add-by-default import; replace only after an explicit confirmation; import history and an already-loaded count on Transactions | `src/data/merge.py` (new), `app/utils/session.py` (`append_data`), `app/components/upload.py`, `app/pages/transactions.py` | `tests/unit/test_merge.py`; `tests/integration/test_csv_upload.py::test_append_keeps_existing_data_and_replace_needs_confirmation`; browser 26–27 | FIXED |
| MA3-02 | Generated IDs = hash(canonical content, occurrence index); the row number is no longer used (D-29) | `src/data/ingestion.py` (`generated_ids`) | `test_generated_ids_do_not_depend_on_row_position`, `test_identical_purchases_in_one_file_stay_distinct`; the earlier `test_ids_are_deterministic_across_reuploads` still passes | FIXED |
| MA3-03 | "Compare this month with last month": relative months resolved and stated | `intent_detection.py`, `query_executor.py`, `response_generator.py` | `test_compare_this_month_with_last_month`; browser 29 | FIXED |
| MA3-04 | Highest-months pattern accepts "which months … highest" (it was answered as total spending) | `intent_detection.py` | `test_highest_months_question_is_not_answered_as_total_spending`; browser 28 | FIXED |
| MA3-05 | New `savings_capacity` intent: the advisor surplus, its basis and the unknowns | `advisor_intents.py` | `test_how_much_can_i_save_uses_the_advisor_surplus_and_states_unknowns` | FIXED |
| MA3-06 | New `flag_explanation` intent: the engine's per-candidate evidence; "review recommended" | `advisor_intents.py` | `test_why_flagged_shows_the_engine_evidence_and_never_claims_fraud` | FIXED |
| MA3-07 | New `indicator_explanation` intent: value, formula and reading; no combined score | `advisor_intents.py` | `test_indicator_explanation_gives_formula_and_engine_value`, `test_generic_indicator_question_lists_all_without_a_combined_score` | FIXED |
| (clarify) | One-word questions get a clarifying reply instead of a guess | `intent_detection.py`, `response_generator.py` | `test_bare_ambiguous_question_asks_for_clarification` | ADDED |
| MA3-08 | `server.address = 127.0.0.1` in the config and the launcher | `.streamlit/config.toml`, `scripts/run_application.py` | `tests/integration/test_launcher.py` (connecting through the network address fails); before the fix, HTTP 200 was measured through the network address | FIXED |
| MA3-09 | Launcher preflight (files, Python, Streamlit), port and running-instance detection, health wait, browser open, Ctrl+C handling; `run.bat` checks `.venv` | `scripts/run_application.py`, `run.bat`, `run.ps1` | `test_launcher_is_local_only_and_never_starts_a_duplicate`, `test_launcher_reports_a_port_used_by_another_program` | FIXED (Linux-tested) |
| MA3-10 | `setup.bat` finds 3.12 via `py -3.12` or `python`; `.venv` reused, never deleted; version check; project-file and dataset report | `setup.bat`, `setup.ps1`, `scripts/setup_environment.py` | fresh install (setup + re-run reuse); `test_windows_scripts_call_the_project_entry_points` | FIXED (Windows NOT TESTED) |
| MA3-11 | `forecast_category` on every product estimate; the HW2 model labelled experimental, with correct post-hoc wording | `inference.py`, `ai_predictions.py`, `advisor_intents.py` | `test_every_product_forecast_states_its_category`; browser 30 | FIXED |
| MA3-12 | Reclassified: not a defect (already documented); re-derived and confirmed | `scripts/audit/anomaly_derived_metrics.py` | match with the saved values = true | VERIFIED |
| MA3-13 | Formula neutralisation in CSV export | `app/utils/exports.py` | `test_csv_export_neutralises_spreadsheet_formulas` | FIXED |
| MA3-14 | Requested documents created (guides and pointers) | `docs/*_GUIDE.md`, `SECURITY.md`, `PRIVACY.md`, `TEST_RESULTS.md`, `ACADEMIC_TRACEABILITY.md` | case-collision check (none) | FIXED |
| MA3-15 | Currency rejection message names ISO 4217 | `app/utils/validation.py` | reviewed | FIXED |
| MA3-16 (found during the audit) | My rewrite of `setup.bat`, `run.bat` and their `.ps1` twins had dropped the repository's CRLF line endings | the same 4 files restored to CRLF | `test_windows_batch_files_use_crlf_line_endings` | FIXED |
