# Test Results

| Run | Environment | Commit | Passed | Failed | Skipped | Evidence |
|---|---|---|---|---|---|---|
| Baseline before the master audit | dev, dataset present | `2cca378` | 125 | 0 | 0 | `baseline_pytest.txt` |
| **Final development run** | dev (CPython 3.12.3), dataset and derived data present | `0952509` working tree | **177** | **0** | **0** | `logs/testing/pytest_20261127T064630Z.log` |
| **Fresh clone of `0952509`** | new clone + new venv with `python3.12 scripts/setup_environment.py` (24 s); **no dataset** | `0952509a50302410624240b124d4d7a5c3c7c5ce` | **173** | **0** | **4** | `freshclone_final/pytest.txt` |

**The 4 fresh-clone skips are data-dependent and say why:**
* L3 eligibility and L11 disjoint panels: "splits not built";
* L10 injections: "anomaly experiment outputs or derived data not present";
* fresh-process reproduction of the recorded predictions: "panel not built".

All 4 pass in the development run. Skipped tests are **not** counted as passed.

**Composition (177 tests):** 107 unit, 47 integration (AppTest pages, upload, pipeline, model loading), 23 regression (leakage, reproducibility, financial correctness, repository completeness, security).

**Added in this audit (125 → 177):**
* insights: 6;
* advisor: 8;
* assistant intents: 5;
* security: 10 parametrized;
* ingestion: overflow 2, delimiters 4, encodings 1;
* upload component: 2; app-path overflow: 1;
* AppTests: analytics, overview, advisor ×2, settings ×2, import summary, and 2 more pages in the render tests;
* outlook: 2;
* artifact verification without data: 1.

| Other check | Result | Evidence |
|---|---|---|
| `scripts/verify_artifacts.py` (dev, derived data) | exit 0; 7/7 PASS | `logs/execution/master_verify_artifacts.log` |
| `scripts/verify_artifacts.py` (fresh clone, demo sample) | exit 0; 7/7 PASS | `freshclone_final/verify_artifacts.txt` |
| Real-browser workflows | 21/21 (dev and fresh clone) | `BROWSER_TEST_RESULTS.md` |
| `ruff check --select F` (pyflakes rules) | clean | final run |
| `git diff --check` | clean | final run |
| `pip-audit` | no known vulnerabilities | `reports/audit/pip_audit.txt` |
| Dataset SHA-256 after all work | `b18c8359…7c17` (unchanged) | re-hashed |
