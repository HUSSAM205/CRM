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
| Quality-gate experiment (E2-QG) | `python scripts/research/forecast_quality_gate.py` (pre-registered protocol in its docstring; about 200 s, 0.74 GB) |
| Audit | `audit.bat` / `audit.ps1`: dataset identity, manifest, 9,488-check reconciliation, artifact reload, tests |
| Feature schema / preprocessing / model versions | `artifacts/*/*/<version>/feature_schema.json` and `metadata.json`; preprocessing config `configs/preprocessing.yaml`; registry `artifacts/metadata/model_registry.json` |
| App | `python scripts/run_application.py` |

Verified: saved artifacts reload in a **fresh process** and reproduce the recorded test predictions exactly (`tests/regression/test_reproducibility.py`, `scripts/verify_artifacts.py`). A full rerun of the preprocessing path gives identical tables (refactor regression check in `KNOWN_ISSUES.md`).

A fresh clone **without** the dataset installs, passes every test except the data-dependent ones (they skip with a stated reason), loads all models and runs the app and all browser workflows (`reports/final_master_audit/TEST_RESULTS.md`).

## Supplementary experiments (master audit 2)

| Step | Command |
|---|---|
| Download Dataset B (pinned revision; SHA-256 checked) | `.venv/bin/python scripts/download_supplementary.py` |
| Dataset B audit | `.venv/bin/python scripts/research/dataset_b_audit.py` |
| E2-B forecasting | `.venv/bin/python scripts/research/forecast_dataset_b.py`, then `forecast_dataset_b_checks.py` (bootstrap and guard) |
| E3-B anomaly | `.venv/bin/python scripts/research/anomaly_dataset_b.py` |
| Dataset C experiments | `.venv/bin/python scripts/research/controlled_synthetic.py` (no download) |
| PersonaLedger demo sample | `.venv/bin/python scripts/prepare_personaledger_demo.py` |
| Laptop benchmark | `benchmark.bat` / `benchmark.ps1` → `reports/laptop_benchmark.json` |
