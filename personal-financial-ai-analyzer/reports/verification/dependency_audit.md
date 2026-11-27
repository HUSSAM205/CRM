# Dependency Audit

Generated 2026-11-27 03:17 UTC.

| Item | Result |
|---|---|
| Direct dependencies (`requirements.txt`) | 14, all pinned, all import |
| Full lock (`requirements-lock.txt`, Linux venv) | 67 packages |
| Consistency check | `All installed packages are compatible` |
| Windows x64 / CPython 3.12 resolution (binary wheels only) | 60 packages resolved, PASS |
| Packages added beyond the HW2 Table 6.1 tool list | PyYAML (configs), joblib (model persistence), psutil (memory guard), matplotlib (static figures), requests (download) |
| GPU / CUDA packages | none |
| Network services used at runtime | none (the app runs fully locally) |

Versions were chosen by the resolver as the current stable releases on 2026-11-27 and then frozen. They were not blindly upgraded afterwards.
