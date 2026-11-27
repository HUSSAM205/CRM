# Test Results (master audit 2)

| Run | Environment | Commit | Passed | Failed | Skipped | Evidence |
|---|---|---|---|---|---|---|
| Baseline (start of master audit 2) | dev, datasets present | `40f366c` | 177 | 0 | 0 | `BASELINE_STATE.md` |
| **Final development run** | dev, CPython 3.12.3, Datasets A and B present | `09c1ce4` | **196** | **0** | **0** | `logs/testing/pytest_20261127T120859Z.log` |
| **Fresh clone of the final code** | new clone + `python3.12 scripts/setup_environment.py` (23 s); **no datasets** | `09c1ce4a679bbae87c96a44ce95df59c4d9c3604` | **192** | **0** | **4** | `freshclone_final/pytest.txt` |

**Fresh-clone skips** (data-dependent, each with a stated reason, never counted as passed):
* L3 and L11 need the splits;
* L10 needs the anomaly outputs;
* the reproduction test needs the panel.

**Composition of the 196 tests:** unit, integration (AppTest pages, upload, model loading, pipeline) and regression (leakage incl. the E2-B leakage test, reproducibility, correctness, repository completeness incl. the `data/supplementary` guard, security).

**Added in master audit 2 (177 → 196):**
* E2-B: feature parity, product routing, PersonaLedger demo end to end, E2-B leakage;
* Dataset C: 3 tests;
* M-12 currencies;
* Advisor: 5 known-answer tests plus the goal-edit AppTest;
* Assistant: 4 tests plus the context/remaining-budget AppTest.

| Other check | Result | Evidence |
|---|---|---|
| `verify_artifacts.py` (dev, derived data) | exit 0, 8/8 | `logs/execution/master2_verify_artifacts.log` |
| `verify_artifacts.py` (fresh clone, demo samples) | exit 0, 8/8 | `freshclone_final/verify_artifacts.txt` |
| Real-browser workflows | 24/24 (dev and fresh clone) | `BROWSER_TEST_RESULTS.md` |
| `ruff --select F` | clean | final run |
| `git diff --check` (excluding `.bat` CRLF) | clean | final run |
| `pip-audit -r requirements.txt` | no known vulnerabilities | `pip_audit.txt` |
| Dataset A SHA-256 | `b18c8359…7c17` (unchanged) | re-hashed |
| Dataset B SHA-256 (2 files) | equal to the official LFS hashes | `scripts/download_supplementary.py` |
| Windows-insensitive filename collisions | 0 | `git ls-files` case check |
