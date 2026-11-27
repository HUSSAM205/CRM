# Security

**Scope:** a local, single-user prototype (HW1 C2). Full control list and residual risks: `SECURITY_AND_PRIVACY.md`.

| Area | Control |
|---|---|
| Network | The server listens on 127.0.0.1 only. The launcher never starts a second server. There is no authentication, so do not expose it on a network |
| Uploads | ≤ 50 MB and ≤ 1,000,000 rows; binary or empty files are refused; per-row and per-file numeric bounds (no int64 overflow); the file name is display text only, never a path |
| Rendering | uploaded text is Markdown-escaped; assistant answers are plain text; no HTML is rendered from data |
| Exports | spreadsheet formulas in text cells are neutralised |
| Models | loaded only from the project's `artifacts/` registry |
| Errors | only error types are shown in the browser (no tracebacks or data) |
| Dependencies | `pip-audit -r requirements.txt`: no known vulnerabilities (2026-11-27) |
| Execution | the assistant only pattern-matches text; there is no eval, exec, shell or network call in the app |

Tests: `tests/regression/test_security.py`, `tests/integration/test_launcher.py`, `tests/integration/test_csv_upload.py`.
