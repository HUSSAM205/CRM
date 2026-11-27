# Security Audit (Gate I)

Controls and residual risks: [`docs/SECURITY_AND_PRIVACY.md`](../../docs/SECURITY_AND_PRIVACY.md).

| Test area (master audit 12.2) | Result | Evidence |
|---|---|---|
| Path traversal and malicious file names | names are display-only and escaped | `test_uploaded_file_names_are_never_used_as_paths`, `test_malicious_names_are_escaped_for_markdown` |
| Oversized uploads | > 50 MB or > 1M rows refused with a message | `test_too_large_file_rejected_with_size_message` |
| Invalid, binary or empty CSV; malformed rows | controlled errors; every row accounted for | `test_ingestion.py`, `test_validation.py`, `test_binary_and_empty_uploads_are_controlled` |
| Overflow (row and file totals) | refused (A-01, **M-02**) | regression tests |
| Unsafe HTML and Markdown injection | escaped; plain-text answers | A-03 tests |
| Cross-session leakage | isolated `st.session_state`; a reload clears it | `test_sessions_are_isolated`; browser task 16 |
| Cross-account leakage | all views and assistant answers scoped to one account and currency | browser task 13; assistant isolation test |
| Error-message leakage | `showErrorDetails = "type"` | `test_error_details_are_not_shown_to_users` |
| Unsafe deserialization | joblib only from registry paths inside `artifacts/` | `test_model_loading_only_from_project_artifacts` |
| Dependency vulnerabilities | **No known vulnerabilities** (`pip-audit -r requirements.txt`, 2026-11-27) | `reports/audit/pip_audit.txt` |
| Secret exposure | 0 secret-like strings in tracked files; `.env` ignored | `reports/audit/static_security_scan.txt` |
| Raw transactions in logs | 0 transaction or account IDs in app and test logs; redaction filter tested | `test_log_redaction_masks_amounts_and_identifiers` |
| External transmission | none (no network imports in app/src; telemetry off) | `test_no_network_or_shell_calls_in_application_code` |
| Retention and deletion | expiry and "Delete" purge data, budgets, goals, facts and history | retention tests; browser tasks 12 and 22 |
| Temporary files | the app writes none; the browser-test fixture uses the OS temp dir (M-01) | `test_app_never_writes_uploads_to_disk` |

**Residual risks:**
* No authentication, so the app is for local use only.
* Earlier commits contain the ephemeral container IP in startup logs (history not rewritten).
* No parser fuzzing.
