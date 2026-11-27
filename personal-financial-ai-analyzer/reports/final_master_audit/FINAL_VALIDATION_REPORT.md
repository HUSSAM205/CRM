> **Superseded (2026-11-27, master audit 2)** by [`FINAL_MASTER_AUDIT.md`](FINAL_MASTER_AUDIT.md). Kept unchanged below as the record of the first master audit.

# Final Validation Report: Gates A–M (master audit, 2026-11-27)

**Final status: READY WITH DOCUMENTED LIMITATIONS.**

It is not "ready for submission", because of these mandatory items:
* the Windows execution is NOT TESTED;
* HW1 P5 (responsiveness on the final hardware) is PARTIAL;
* the target-hardware performance is not measured.

Under the acceptance rules none of these is a FAIL. Forecasting ML is **REJECTED** with a documented, tested fallback, which the rules allow.

Code state: `0952509` (fresh-clone verified). Later commits change reports only. Environment: cloud container, CPython 3.12.3.

| Gate | Status | Evidence | Command(s) | Actual result | Remaining limitation |
|---|---|---|---|---|---|
| **A** Repository integrity | **PASS** | `REPOSITORY_INVENTORY.md`, `repository_inventory.json`, `freshclone_final/` | `scripts/audit/repo_inventory.py`; `test_repository_completeness.py`; fresh clone | 0 broken imports, 0 hardcoded paths, 0 deprecated APIs; no data, venv or secrets tracked; checkpoint tags `audit-start-…`, `master-audit-start-…`; no force-push or history rewrite; the fresh clone passes | 2 unused modules kept on purpose (D-21) |
| **B** Dataset integrity | **PASS** | `DATASET_FORENSIC_REPORT.md`, `DATASET_MANIFEST.json`, `DATA_QUALITY_REPORT.json` | `verify_dataset.py`, `audit/dataset_manifest.py` | SHA-256 re-hashed and equal to the official LFS oid; 50,000,000 rows, 9 columns; 27/27 checks; 8/8 advertised properties; full audit with no sampling; 0 unexplained row loss (50M in = 50M accounted) | commercial licence BLOCKED (legal) |
| **C** Financial correctness | **PASS** | `FINANCIAL_RECONCILIATION.md`, `financial_reconciliation.json` | `audit/reconcile_granular.py`; unit and regression tests | 9,488/9,488 exact (currency × month, × category, records, accounts); curated cases 100% exact; transfers neutral; refunds net; pending, failed and reversed excluded; overflow refused (A-01, M-02 fixed) | no currency conversion (by design) |
| **D** Machine learning | **PASS** (forecasting ML: **REJECTED** with fallback) | `FORECASTING_EXPERIMENTS.md`, `MODEL_COMPARISON.csv`, `docs/FORECASTING.md` | `research/forecast_quality_gate.py` (guarded) | split preserved; rolling origin; zero and median baselines; zero-prediction root cause established (data characteristics); selection on validation only; GBR not presented as successful; the deterministic outlook is deployed, with interval coverage 81.9% on test | no model has temporal skill on this data |
| **E** Anomaly detection | **PASS** (model status PARTIAL: weak) | `ANOMALY_EXPERIMENTS.md` | E3 outputs; independent recomputation | reproducible injection (3 rates × 3 seeds, labels isolated, test-period only); metrics recomputed (\|Δ\| = 0); FPR and F1 documented; alerts worded as review recommendations | F1@k ≤ 0.041; hour and category anomalies undetectable |
| **F** Analyzer | **PASS** | `docs/ANALYZER.md`, `test_insights.py`, AppTests | pytest; browser 5, 6, 13, 17 | page values equal the module values; filters (period, account, currency, category, type, status, date) work; charts come from `Summaries` | recurring detection is heuristic (candidates) |
| **G** Advisor | **PASS** | `ADVISOR_VALIDATION.md` | `test_advisor.py`; browser 18–20 | known-answer tests for goals, milestones, scenarios, affordability verdicts and ranking; missing context stated; never confirms affordability without a balance | rules-based; session-only goals |
| **H** Assistant | **PASS** | `ASSISTANT_VALIDATION.md` | assistant tests; browser 10, 11, 21 | 13 intents correct; unsupported and injection inputs get the fixed reply; account isolation (two-account test); read-only; no execution | English patterns only |
| **I** Privacy and security | **PASS** | `SECURITY_AUDIT.md` | `test_security.py`, upload tests, `pip-audit` | uploads in memory only; retention and deletion (incl. goals and facts); 0 IDs in logs; no network; 0 known vulnerabilities; 0 secrets | no authentication (local use) |
| **J** Performance | **PARTIAL** | `PERFORMANCE_BENCHMARKS.md`, `performance_benchmarks.json` | `audit/benchmark_master.py`; guarded runs | every job ≤ 1.86 GB under a 4 GB guard; no retraining in the app; inference 0.4–20 ms warm; model load 1.2–1.5 s cold; pages 0.12–1.5 s first render | **target laptop not measured** |
| **K** UI and browser | **PASS** | `BROWSER_TEST_RESULTS.md`, `reports/screenshots/` | `node scripts/ux/ux_tasks.mjs` | 21/21 (dev and fresh clone); every page tested; underlying values checked; screenshots of 8 pages and 21 states | scripted, no human study; date filter verified by AppTest |
| **L** Academic compliance | **PARTIAL** | `REQUIREMENTS_TRACEABILITY.md`, `docs/requirements_traceability.md` | `project_inventory.py` | HW: 67 PASS / 1 PARTIAL (P5) / 1 N/A (P3) / 0 FAIL of 69; all 9 HW1 functional requirements PASS; HW2 methodology preserved (E2 frozen; E2-QG separate) | P5 PARTIAL |
| **M** Documentation and delivery | **PARTIAL** | 16 required docs, `REPRODUCIBILITY_GUIDE.md`, `WINDOWS_VALIDATION.md` | fresh clone with `python3.12` | Linux install, tests, model loading, app and browser all pass from a clean clone; dataset acquisition and verification scripted; reports present; pushed | **Windows NOT TESTED** |

**Gate tally:** 10 PASS (A–I, K), 3 PARTIAL (J, L, M), 0 FAIL, 0 NOT TESTED at gate level. The NOT TESTED Windows sub-item is inside M.

Master-audit product requirements: 38 PASS / 1 PARTIAL / 1 NOT TESTED of 40 (`REQUIREMENTS_TRACEABILITY.md` §2). The three denominators (69 HW rows, 40 product items, 13 gates) are separate and never added together.

**Acceptance-rule check:**
* no unresolved critical financial defect;
* no leakage defect: 7/7 leakage tests pass with data;
* no cross-account leak;
* no fabricated result: every number above comes from a file listed in this package;
* no PASS without evidence;
* rejected models are labelled REJECTED.
