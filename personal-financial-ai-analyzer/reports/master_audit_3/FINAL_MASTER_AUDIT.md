# Final Master Audit (master audit 3)

**Engineering verdict: READY WITH LIMITATIONS.**
* The Analyzer, Advisor, Predictive Intelligence routing, anomaly review, local Assistant, security controls and local launch are implemented and verified on Linux, with reproducible evidence.
* **Windows execution and the student laptop are NOT TESTED.**

**Academic verdict: NOT READY FOR UNIVERSITY SUBMISSION.**
* The original experiments E1–E4 are intact and reproducible.
* Report-level items remain open:
  * the HW1 bibliography (two references unresolved);
  * Tables 9.1 and 9.2 to fill in the final report;
  * P5 not measured on the laptop;
  * R3 not done.
* See `FINAL_ACADEMIC_TRACEABILITY.md` and `reports/final_master_audit/ACADEMIC_SUBMISSION_REVIEW.md`.

**About this audit:**
* **Date:** 2026-11-27.
* **Environment:** Linux cloud container, Intel Xeon @ 2.10 GHz, 4 logical CPUs, 16.9 GB RAM, CPython 3.12.3.
* **Starting commit:** `2eab394`. All changes in this audit are **uncommitted**: no commit or push was authorised.
* **Re-run:** every PASS below was re-run in this audit. No PASS was carried over from an earlier report.

## Gates

| Gate | Result | Evidence (re-run in this audit) | Remaining limitation |
|---|---|---|---|
| **A** Repository integrity | PASS | Baseline recorded (`REPOSITORY_BASELINE.md`); earlier uncommitted work preserved; nothing deleted; HW PDFs unchanged (SHA-256 checked) | All master-audit-3 work is uncommitted (5 new files registered with `git add --intent-to-add` only, for the completeness test) |
| **B** Original academic compliance | PARTIAL | E1–E4 definitions, split, metrics and selection rule unchanged; outputs and models never regenerated (git history); E2-B and E3 numbers reproduced read-only | HW1 P5 partial (no laptop measurement, no numeric threshold in HW1); R3 not performed; report-level gaps (`ACADEMIC_SUBMISSION_REVIEW.md`) |
| **C** Dataset integrity | PASS | Dataset A: `verify_dataset.py` OVERALL PASS (50,000,000 rows, 9 columns, SHA-256 = live HF LFS). Dataset B: 2/2 file hashes PASS; HF head revision is still `c90078ae…`; licence `cc-by-4.0` | All data is synthetic. Candidates OpenML 43627, UCI Wholesale and IEEE DataPort rejected (`DATASET_CANDIDATES.md`) |
| **D** Analyzer | PASS | Full-data reconciliation 9,488/9,488, 0 mismatches; unit, integration and browser tests; **new:** append/import workflow with duplicate prevention and confirmed replacement (MA3-01/02) | Session-only data (by design) |
| **E** Advisor | PASS | `test_advisor.py` known answers; browser 18–20, 25; balance never inferred; affordability never confirmed with unknown facts | Rules-based; no interest modelling |
| **F** Predictive Intelligence | PASS (requirement) | Only validated or deterministic outputs reach the product; every result states its type (MA3-11); E2-B reproduced exactly: MAE 971.34 vs 1,022.66 (−5.02%), 80% coverage 77.65% (`e2b_reproduction.json`) | The gain is small and validated on **synthetic** Dataset B only; on Dataset A no ML model beats a zero forecast (post-hoc E2-QG) |
| **G** Anomaly detection | PASS (requirement) | Alerts labelled "Unusual transaction — review recommended", never fraud. E3 F1/FPR re-derived from saved scores and identical to the docs (`anomaly_derived_metrics.json`). Identity theft (E3-B) at chance level, preserved | Detection is weak: E3 AUC 0.56–0.59, and the per-account IF specified by HW2 lost to the robust z-score |
| **H** Local Assistant | PASS | 5 defects fixed (MA3-03..07), including one **wrong answer**; 14 new known-answer tests; refusal paths; account isolation; browser 10, 11, 21, 24, 28, 29 | English patterns only |
| **I** Integration | PASS | Dashboard and assistant share `Summaries`; the advisor and assistant use the same engine; 29/29 browser tasks | — |
| **J** Security and privacy | PASS (tested scope) | **New:** localhost-only binding (it was reachable over the network before: measured HTTP 200), no duplicate server, CSV formula neutralisation. `pip-audit`: no known vulnerabilities. Upload, rendering, deletion and isolation tests pass | No authentication (local single-user tool); no fuzzing beyond the tested cases |
| **K** Performance | PARTIAL | Container: server start 0.73 s cold; page first render 0.11–1.18 s; 200k-row ingest 0.45 s; peak RSS ≤ 0.36 GB (`benchmark_container.json`) | **Not measured on the student laptop**; no P5 threshold is defined in HW1 |
| **L** Unit and integration tests | PASS | **223 passed, 0 failed, 0 skipped** (`logs/testing/pytest_20261127T133709Z.log`) | — |
| **M** Real-browser tests | PASS | **29/29** tasks, 0 errors, Chromium (Playwright), screenshots; phone width (390 px): no horizontal overflow on 8 pages | Phone check covered empty-state pages only; scripted, with no human participants |
| **N** Fresh installation | PASS (Linux) | Clean copy of the tracked tree: setup 25 s, **219 passed / 4 skipped** (data-dependent, reasons stated); launcher healthy; second launch refused a duplicate | Linux only |
| **O** Windows setup | NOT TESTED | Static review of all 6 `.bat` and 6 `.ps1`; CRLF enforced by a test; entry points exist (test); the Python logic they call was executed on Linux | No Windows machine available |
| **P** Windows execution | NOT TESTED | — | Must be run once on the laptop (`docs/WINDOWS_INSTALLATION.md`) |
| **Q** Documentation | PASS | All requested documents exist (8 new guide or pointer files); docs match the code; no case-only file-name collisions | — |
| **R** Academic traceability | PARTIAL | `FINAL_ACADEMIC_TRACEABILITY.md` (F1–F9, P1–P5, R1–R8, E1–E4); citations verified through index pages (`CITATION_VERIFICATION.md`) | `yang2026` and `[9]` unresolved; the HW1 bibliography must be rebuilt in the final report |
| **S** Reproducibility | PASS | Artifacts 8/8 reload with identical predictions; E2-B exact; reconciliation exact; fresh install | Linux only |
| **T** Localhost practical operation | PARTIAL | The app runs at **http://localhost:8501** (bound to 127.0.0.1) in this **cloud container**; health `ok`; browser tasks passed against it | The user's laptop cannot reach this container's localhost; running on the laptop is NOT TESTED |

## Acceptance matrix (requirements of this audit)

| Req | Requirement | Implementation | Test evidence | Result | Remaining limitation |
|---|---|---|---|---|---|
| R-01 | Preserve the original dataset and HW files | read-only checks | `verify_dataset.py` PASS; PDF hashes | PASS | — |
| R-02 | E1–E4 unchanged and distinguishable | frozen outputs; supplementary IDs | git history; `ACADEMIC_SUBMISSION_REVIEW.md` §2 | PASS | — |
| R-03 | Explicit append/import, duplicate prevention, confirmed replace | `src/data/merge.py`, `upload.py`, `session.py` | `test_merge.py` (6), AppTest, browser 26–27 | PASS | — |
| R-04 | ISO currencies; TRY not misread | `schema.py` (M-12) | `test_any_active_iso_currency…`; stale message fixed (MA3-15) | PASS | — |
| R-05 | Calculations independently verified | reconciliation, fixtures | 9,488/9,488; known-answer tests | PASS | — |
| R-06 | Advisor never infers a balance; affordability conservative | `advisor/*` | `test_advisor.py`; browser 20 | PASS | — |
| R-07 | Only validated models in product; type disclosed | `inference.forecast_product` | `test_every_product_forecast_states_its_category`; browser 30 | PASS | synthetic validation only |
| R-08 | E2-B metrics reproduced | `scripts/audit/reproduce_e2b.py` | `e2b_reproduction.json` match = true | PASS | — |
| R-09 | Anomaly: precision, recall, F1, FPR; never fraud | `anomaly_scoring.py`; derived metrics | `anomaly_derived_metrics.json`; browser 9 | PASS | weak detection |
| R-10 | Assistant answers the required questions without an API | `src/assistant/*` | `test_assistant_ma3.py` + earlier tests | PASS | — |
| R-11 | Uploaded text rendered safely | `md_escape`, `st.text` | `test_security.py` | PASS | — |
| R-12 | Not exposed to public interfaces | `.streamlit/config.toml`, launcher | `test_launcher.py` | PASS | — |
| R-13 | Offline after setup; no external services | no network calls in `app/` or `src/` | `test_no_network_or_shell_calls…` | PASS | — |
| R-14 | Measured performance, honestly labelled | `benchmark_master.py` | `benchmark_container.json` | PARTIAL | laptop not measured |
| R-15 | Windows scripts ready | `.bat`/`.ps1`, `setup_environment.py`, `run_application.py` | static review + Linux execution + 2 tests | PARTIAL | NOT TESTED on Windows |
| R-16 | Verified citations, none invented | `CITATION_VERIFICATION.md` | index-page verification | PARTIAL | `yang2026` and `[9]` unresolved |

**Files:**
* Defects and their resolution: `DEFECT_RESOLUTION.md`.
* Test counts: `FINAL_TEST_RESULTS.md`.
* Open issues: `FINAL_KNOWN_ISSUES.md`.
* Windows: `WINDOWS_DEPLOYMENT.md`.
* Phase-by-phase validation: `FINAL_VALIDATION_REPORT.md`.
* Delivery checklist: `FINAL_DELIVERY_CHECKLIST.md`.
