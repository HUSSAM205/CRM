# Final Known Issues (master audit 3)

Open items only. The fixed defects are in `DEFECT_RESOLUTION.md`; the full history is in `KNOWN_ISSUES.md` at the project root.

| # | Issue | Type | Status | What closes it |
|---|---|---|---|---|
| F-01 | Windows setup and execution never run | Deployment | NOT TESTED | Run `setup.bat`, `test.bat`, `run.bat` on the laptop (`docs/WINDOWS_INSTALLATION.md`) |
| F-02 | HW1 P5: no laptop measurement; HW1 defines no threshold | Academic / performance | PARTIAL | Define a threshold in the report, then run `benchmark.bat` |
| F-03 | HW1 R3: no validation on de-identified real cases | Academic | NOT TESTED | Disclose it, or obtain permissible de-identified data |
| F-04 | All three datasets are synthetic | Validity | Limitation | Disclose: there is no real-world accuracy or fraud claim |
| F-05 | Forecasting ML has no skill on Dataset A (a zero forecast is better); the E2-B gain on Dataset B is small (−5% MAE) | Model | Limitation | Disclosed in the app (result type) and in the docs |
| F-06 | Unusual-transaction ranking is weak (AUC 0.56–0.59); identity theft is at chance level | Model | Limitation | Shown only as review candidates |
| F-07 | HW1 bibliography: `yang2026` and `[9]` unresolved | Academic | Open | The student supplies or removes them (`CITATION_VERIFICATION.md`) |
| F-08 | HW2 Tables 9.1 and 9.2 empty in the submitted PDF | Academic | Open | Fill them in the final report (values in `ACADEMIC_SUBMISSION_REVIEW.md` §6–7) |
| F-09 | No authentication; single-user local tool | Security | Accepted (HW1 C2) | The server is bound to 127.0.0.1 |
| F-10 | Phone-width check covered empty-state pages only; no human usability study | UX evidence | Limitation | — |
| F-11 | `audit.ps1` and `benchmark.ps1` are stored with LF endings (PowerShell accepts LF); all `.bat` files are CRLF (tested) | Deployment | Informational | — |
| F-12 | Every master-audit-3 change is uncommitted | Repository | Awaiting authorisation | The user authorises commit and push |
| F-13 | Earlier commits contain a cloud container's temporary IP in old Streamlit logs; history not rewritten (no force-push, by rule) | Privacy | Accepted | — |
