# Reproducibility

| Item | Value / location |
|---|---|
| Python | 3.12.3 (`.python-version`) |
| Dependencies | `requirements.txt` (direct, pinned) and `requirements-lock.txt` (67 packages, verified env) |
| Dataset | HF `ziadatalabs/FreeFinancialTransactions50M`, commit `98cf38f9…`, SHA-256 `b18c8359…` (`docs/dataset_provenance.md`) |
| Seeds | 42 primary; 43 and 44 robustness (`configs/experiments.yaml`). GBR `random_state` = 42 with early stopping off. IF `random_state` = 42 |
| Splits | `configs/experiments.yaml`. Actual counts in `data/processed/splits/split_metadata.json` |
| Model parameters | `artifacts/<kind>/<model>/<version>/metadata.json` |
| Commands | `python scripts/run_full_pipeline.py` (all steps). Individual steps: `scripts/{download_dataset,verify_dataset,run_audit,investigate_ledger,run_preprocessing,train_forecasting,train_anomaly,evaluate_models,verify_artifacts,run_all_tests,generate_final_evidence}.py` |
| App | `python scripts/run_application.py` |

Verified: saved artifacts reload in a **fresh process** and reproduce the recorded test predictions exactly (`tests/regression/test_reproducibility.py`, `scripts/verify_artifacts.py`). A full rerun of the preprocessing path gives identical tables (refactor regression check in `KNOWN_ISSUES.md`).
