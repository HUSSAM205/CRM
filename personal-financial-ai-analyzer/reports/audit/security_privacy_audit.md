# Security and Privacy Audit

| Check | Method | Result | Status |
|---|---|---|---|
| Dependency vulnerabilities | `pip-audit -r requirements.txt` | "No known vulnerabilities found" (`pip_audit.txt`) | PASS |
| Secrets in tracked files | Pattern scan of every tracked text file | 0 matches (`static_security_scan.txt`); `.env` ignored; only `.env.example` tracked | PASS |
| Network calls from the app | Import scan of `app/` and `src/` | 0. Only `src/data/download.py` (the offline download script) imports `requests` | PASS |
| Telemetry | `.streamlit/config.toml` | `gatherUsageStats=false` (A-04) | PASS |
| Upload storage | `test_app_never_writes_uploads_to_disk`; code review | Uploads stay in session memory only; retention with auto-purge; "Delete my data now" | PASS |
| Session isolation | `test_sessions_are_isolated`; UX task 16 | Separate sessions share nothing; a reload clears data | PASS |
| Raw values in logs | Redacting logger; ID-pattern scan of all app and test logs | 0 transaction or account IDs in logs | PASS |
| Upload limits | Config plus tests | 50 MB / 1M rows, with a controlled error beyond them | PASS |
| Malicious input | Overflow amount (A-01, fixed); Markdown/HTML injection (A-03, fixed); prompt-injection text to the assistant gets the unsupported reply (`assistant_probe.txt`) | Controlled | PASS |
| Error disclosure | `showErrorDetails="type"` | No tracebacks or data shown in the browser | PASS |
| External LLM / data sharing | Architecture; grep | None: deterministic assistant | PASS |
| Dataset not uploaded anywhere | Process review | Downloaded from the official source only; never sent out; not in git | PASS |

## Residual risks (documented, not defects)

* Streamlit has no authentication. It is designed for local, single-user use (HW1 C2). Do not expose it on a network.
* `data/raw` is unencrypted on disk. It is a public synthetic dataset.
* The upload parser is Polars CSV. Parser-level fuzzing beyond the tested malformed cases was not performed.
* The tracked Streamlit startup logs contained the ephemeral cloud container's network and external URLs (no personal or financial data). They are redacted from this commit on. Earlier commits still contain them, because history is not rewritten.
