# Security and privacy

## Data handling (local-first by default)

| Question | Answer | Enforced by |
|---|---|---|
| What is uploaded? | One CSV file through the browser | Size ≤ 50 MB, ≤ 1,000,000 rows (`configs/app.yaml`); the file's absolute amounts must sum to less than 2⁶² cents (M-02) |
| Where is it processed? | In the memory of the user's Streamlit session on the machine running the app | `app/utils/session.py`; `test_app_never_writes_uploads_to_disk` |
| How long is it kept? | 15 minutes, 1 hour (default) or until the tab closes; "Delete my data now" and "Delete all my data" (Settings) purge immediately: transactions, budgets, goals, entered facts and assistant history | retention and purge tests; browser tasks 12 and 22 |
| Is it used for training? | Never. Models were trained offline on the public dataset only | Training scripts read `data/raw` only |
| External services? | None. No LLM, no telemetry (`gatherUsageStats=false`), no network calls in `app/` and `src/` | `tests/regression/test_security.py` |
| Logs? | Counts and events only; a redaction filter masks amounts and IDs | `test_log_redaction_masks_amounts_and_identifiers`; 0 IDs in app logs |
| Other users? | Each browser session is isolated | `test_sessions_are_isolated`; assistant account-isolation test |

## Application security controls

| Threat | Control | Test |
|---|---|---|
| Malformed, binary or empty CSV | controlled `IngestionError`; row-level reasons | `test_ingestion.py`, `test_validation.py`, `test_security.py` |
| Integer overflow | per-row bound 10¹² (A-01); per-file total bound (M-02) | regression tests that fail before the fix |
| Markdown or HTML injection (file names, categories, questions) | `md_escape`; answers rendered with `st.text` | `test_malicious_names_are_escaped_for_markdown` |
| Path traversal through file names | the upload name is display-only; never used as a path | `test_uploaded_file_names_are_never_used_as_paths` |
| Unsafe deserialization | `joblib.load` only on registry paths inside `artifacts/` (project-owned), in 2 modules | `test_model_loading_only_from_project_artifacts` |
| Arbitrary execution through the assistant | questions are pattern-matched only; no eval, exec or shell in app code | `test_no_network_or_shell_calls_in_application_code`; assistant injection test |
| Error disclosure | `showErrorDetails = "type"` (no tracebacks or data in the browser) | `test_error_details_are_not_shown_to_users` |
| Dependency vulnerabilities | `pip-audit -r requirements.txt` | "No known vulnerabilities found" (2026-11-27) |
| Secrets | none in the repository; `.env` ignored | static scan, 0 matches |

## Residual risks

* **No authentication:** the app is a local, single-user tool (HW1 C2) and must not be exposed on a network.
* The dataset is stored unencrypted on disk; it is public synthetic data.
* Earlier commits contain the cloud container's temporary IP address in Streamlit startup logs. History was not rewritten.
* No parser fuzzing beyond the tested malformed cases.
