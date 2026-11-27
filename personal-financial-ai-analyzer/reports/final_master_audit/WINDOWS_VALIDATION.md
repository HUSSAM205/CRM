# Windows Validation

**Status: NOT TESTED.** No Windows machine was available in this cloud environment, so Windows compatibility is **not** claimed.

What *was* verified:
* the pinned requirements resolve for win_amd64 / CPython 3.12 with wheels only (`reports/verification/requirements-windows-resolved.txt`);
* all four scripts exist: `setup.bat`, `run.bat`, `train.bat`, `audit.bat`, plus `.ps1` equivalents and `test.bat`;
* the Python code uses `pathlib` throughout;
* the hardcoded `/tmp` in the browser script was fixed (M-01);
* the docs were renamed so that no two names differ only in letter case (M-10).

Exact commands and expected outcomes: [`docs/WINDOWS_INSTALLATION.md`](../../docs/WINDOWS_INSTALLATION.md). Expected test result without the dataset: 0 failed, with the data-dependent tests skipped. The Linux fresh-clone reference count is in `TEST_RESULTS.md`.
