# Final Test Results

## Automated tests (pytest)

| Run | Where | Commit | Result | Log |
|---|---|---|---|---|
| Final development run (after all audit fixes and report edits) | Cloud container, with the dataset and derived data present | working tree before the final commit | **125 passed, 0 failed, 0 skipped** (6.8 s) | `logs/testing/pytest_20261127T054014Z.log` (`latest.log`) |
| Previous development run | same | `0da7bbb` + report edits | 124 passed | `logs/testing/pytest_20261127T052933Z.log` |
| **Fresh clone 4 (no dataset), final delivered commit** | Clean clone and new venv | `ed4d45c` | **121 passed, 4 skipped, 0 failed** | `reports/audit/freshclone4_final/pytest.txt` |
| Fresh clone 3 (no dataset) | Clean clone and new venv | `0da7bbb` | **120 passed, 4 skipped, 0 failed** | `reports/audit/freshclone3_after_fix/pytest.txt` |
| Fresh clone 2 | same | `b64e65b` | 119 passed, 3 skipped, **1 failed** (A-09) | `reports/audit/freshclone2_partial_fix/pytest.txt` |
| Fresh clone 1 | same | `157bf5d` | **10 collection errors** (A-08) | `reports/audit/freshclone_before_fix/pytest.txt` |

* The 4 fresh-clone skips are data-dependent (splits, panels and anomaly outputs require the 1.6 GB dataset). They run and pass in the development run.
* Development run 125 = previous 124 plus the A-05 regression test.

**Test growth:**
* 118 before the audit (previously reported).
* 124 in the audit run: + overflow, + date filter, + saved-budget flow, + 2 repository-completeness tests, + 1 budget AppTest.
* 125 now: + ISO-timestamp test.

**Leakage and repository tests,** run verbosely: 9/9 PASSED (`reports/audit/leakage_and_completeness_tests.txt`).

## Other validations

| Check | Result | Evidence |
|---|---|---|
| `python scripts/verify_artifacts.py` | exit 0; every artifact PASS | `logs/execution/audit_verify_artifacts_final.log` |
| Real-browser UX tasks | **15/15**, mean 2.40 s, max 5.88 s (development); **15/15** in fresh clone 4 | `reports/ux_tasks/ux_task_results.json`, `reports/audit/freshclone4_final/ux_results.txt` |
| Date-filter UI | PASS (AppTest, real widget state) | `test_transactions_date_filter` |
| `git diff --check` | clean | final run |
| `pip-audit` | no known vulnerabilities | `reports/audit/pip_audit.txt` |
| Dataset SHA-256 after all audit work | `b18c8359…7c17` (unchanged) | `reports/audit/dataset_immutability.txt` |

The development and fresh-clone runs have different counts because the fresh clone has no dataset. The two are never merged into one number.
