# Environment Verification Report

Generated 2026-11-27 03:17 UTC from `reports/verification/environment.json` (run 2026-11-27T02:54:58.084442+00:00).
**Status: PASS**

| Item | Value |
|---|---|
| Python | 3.12.3 |
| Interpreter | `/home/user/CRM/personal-financial-ai-analyzer/.venv/bin/python` |
| Inside project .venv | True |
| Platform | Linux-6.18.44-fc-v880-x86_64-with-glibc2.39 |
| Import failures | 0 |
| Dependency consistency | `All installed packages are compatible` |
| RAM total / available | 16.87 / 14.77 GB |
| Disk free | 61.32 GB |
| Logical CPUs | 4 |
| Tools | git, uv, curl, sha256sum |
| CUDA / GPU | not present and not required (all models are CPU scikit-learn/statsmodels) |

## Direct dependencies (imported successfully)
| Package | Version |
|---|---|
| polars | 2.2.0 |
| pyarrow | 26.0.1 |
| pandas | 3.1.1 |
| numpy | 2.5.5 |
| scikit-learn | 1.9.1 |
| statsmodels | 0.15.0 |
| streamlit | 1.67.0 |
| plotly | 7.2.0 |
| PyYAML | 6.0.4 |
| joblib | 1.6.0 |
| psutil | 7.2.2 |
| pytest | 9.2.0 |
| matplotlib | 3.11.2 |
| requests | 2.34.2 |

## Windows target
* `uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.12 --only-binary :all:`
  **resolved successfully** (wheels only, no source builds): `reports/verification/requirements-windows-resolved.txt`.
* An actual install on the user's Windows laptop is **NOT TESTED** (no access from the cloud). `setup.ps1` / `setup.bat` are provided.
