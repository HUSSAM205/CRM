> **Superseded (2026-11-27)** by the master audit in `reports/final_master_audit/` (Analyzer & Advisor scope, gates A–M). Kept unchanged below for the record.

# Final Validation Report: Gates A–P (independent final audit, 2026-11-27)

**Final project status: READY WITH DOCUMENTED LIMITATIONS.**

It is not READY FOR SUBMISSION, for three reasons:
* HW1 P5 is PARTIAL;
* the Windows install and the user's laptop are NOT TESTED;
* the forecasting and anomaly components pass their protocols but show no or weak scientific skill on this synthetic dataset.

This file supersedes the earlier `reports/final_validation_report.md` ("27/27 PASS"). That claim was **overstated**: see `EVIDENCE_AUDIT.md`.

Environment: cloud container (x86_64 Linux, CPython 3.12.3, 4 vCPU, about 16.9 GB RAM). Branch `claude/hopeful-noether-t6vfi7`.

| Gate | Status | Evidence | Command | Actual result | Remaining limitations |
|---|---|---|---|---|---|
| **A** Academic requirements | **PARTIAL** (68/69 rows satisfied: 67 PASS + 1 justified N/A; 1 PARTIAL) | `REQUIREMENTS_TRACEABILITY.md`, `docs/requirements_traceability.md` | `python scripts/project_inventory.py` | 69 rows: 67 PASS, 1 PARTIAL (P5), 1 N/A (P3), 0 FAIL, 0 NOT TESTED. Two earlier PASS rows were wrong (S7, P1) and are now fixed | P5 laptop responsiveness not measured |
| **B** Dataset identity and integrity | **PASS** | `reports/audit/dataset_identity_audit.md` | `python scripts/verify_dataset.py`; `curl -I` official URL; `sha256sum` | Commit `98cf38f9…`, 1,594,749,644 B, SHA `b18c8359…` (equal to the official LFS etag); 50,000,000 rows; 27/27 checks; unchanged before and after the audit | — |
| **C** Data engineering correctness | **PASS** | `reports/audit/data_engineering_audit.md`, `reconciliation.json` | `python scripts/audit/reconcile_totals.py`; resume test | 54/54 exact integer matches against an independent PyArrow recomputation; resume and determinism 9/9 identical; ISO-T timestamps fixed (A-05) | 0.70% of panel cells are zero-filled before account start (P3) |
| **D** Financial calculation correctness | **PASS** | `reports/audit/financial_calculation_audit.md` | `python -m pytest tests/unit tests/regression/test_financial_correctness.py` | Exact on fixtures, full data and edge cases; overflow crash A-01 **fixed**, with a regression test | Transfers assumed internal (CF-08) |
| **E** Actual ML training verification | **PASS** | `reports/audit/model_training_audit.md`, `training_audit.json` | `python scripts/audit/training_audit.py` (guarded) | Models re-trained from scratch: GBR 100 trees / 800 leaves on 360k (refit 440k) rows; IF 100 trees / 15,262 nodes on 223,654 rows; all metrics reproduce with Δ = 0.0 | Subset training by design (HW1 C3, HW2 6.3); full population checked separately |
| **F** Leakage-free methodology | **PASS** | `tests/regression/test_data_leakage.py`, `docs/leakage_analysis.md` | `python -m pytest tests/regression/test_data_leakage.py` | 7/7 leakage regression tests pass with the data present (L1/L7, L2, L3, L8, L10, L11; `reports/audit/leakage_and_completeness_tests.txt`): forbidden columns absent, train-only eligibility, train-period targets, history statistics ignore scored rows, test-only injections, disjoint panels. The other L-items are design controls or unit-tested (`docs/leakage_analysis.md`) | — |
| **G** Forecasting scientific validation | **PASS** (protocol), **scientific validity: limited** | `reports/audit/forecasting_audit.md` | same as E | Selected GBR: val MAE 26.554 / MASE 0.551; test 27.194 / 0.570. A zero forecast is better (test 25.374 / 0.532). All R² < 0. The full population confirms it | No demonstrable temporal skill (F-1..F-3) |
| **H** Anomaly detection validation | **PASS** (protocol), **scientific validity: weak** | `reports/audit/anomaly_detection_audit.md` | same as E | 1%, seed 42: AUC 0.56–0.59; F1@k 0.008–0.041; FPR about 1%; positive control AUC 0.999 | Not a fraud detector; hour and category scenarios undetectable |
| **I** Model artifact reproducibility | **PASS** | `reports/verification/artifact_verification.json` | `python scripts/verify_artifacts.py` | Exit 0; 6/6 artifacts load in a fresh process and reproduce recorded predictions | Pickle (joblib): load only this repository's own artifacts |
| **J** Complete application workflows | **PASS** | `reports/audit/application_audit.md`, `reports/ux_tasks/ux_task_results.json` | `node scripts/ux/ux_tasks.mjs http://localhost:8501` | 15/15 real-browser tasks; the date filter is verified by AppTest; A-02, A-03, A-04 and A-06 fixed | Scripted, not a human study |
| **K** Assistant correctness and account isolation | **PASS** | `AI_ASSISTANT_AUDIT.md`, `reports/audit/assistant_probe.txt` | `python -m pytest tests/unit/test_assistant.py tests/integration/test_dashboard.py` | Answers equal the dashboard; 5 intents; adversarial inputs get the unsupported reply; budgets scoped per account and currency; UX task 13 isolation | English keywords only |
| **L** Security and privacy | **PASS** | `reports/audit/security_privacy_audit.md`, `pip_audit.txt`, `static_security_scan.txt` | `pip-audit -r requirements.txt`; scans | 0 known vulnerabilities, 0 secrets, 0 network calls in app/src, 0 IDs in logs, telemetry off | No authentication (local single-user design) |
| **M** Resource and performance | **PARTIAL** | `reports/audit/performance_resource_audit.md` | guarded runs; `inference_performance.json` | Peak 1.86 GB under a 4 GB guard; app operations 1–14 ms; first model load 1.3 s | Not measured on the 16 GB laptop |
| **N** Clean installation and fresh clone | **PARTIAL** (Linux PASS; Windows NOT TESTED) | `reports/audit/fresh_install_audit.md` | clone → `python scripts/setup_environment.py` → pytest → app → UX | Clone 4 at the final commit `ed4d45c`: setup 26 s, 121 passed, 4 skipped, UX 15/15, 0 tracebacks. Clone 1 failed (A-08, P0, fixed) | Windows `setup.bat` not executed (steps in `FINAL_DELIVERY_CHECKLIST.md`) |
| **O** Final academic evidence | **PASS** | `reports/final_evidence/`, `docs/final_results.md`, `docs/KNOWN_LIMITATIONS.md` | `python scripts/generate_final_evidence.py` | Tables 9.1 and 9.2 filled from result files; unfavorable findings kept and expanded | — |
| **P** Repository integrity and delivery | **PASS** | `reports/audit/repository_audit.md` | `python -m pytest tests/regression/test_repository_completeness.py`; `git diff --check` | All required files tracked; no data or venv tracked; pushed | 7 modules merged by design |

**Tally of the 16 gates:** 12 PASS (G and H: protocol PASS with limited or weak scientific validity), 3 PARTIAL (A, M, N), 0 FAIL, 0 NOT TESTED. The Windows sub-item of N is NOT TESTED. Gate denominators are not the same as the 69 traced requirements: see `REQUIREMENTS_TRACEABILITY.md`.
