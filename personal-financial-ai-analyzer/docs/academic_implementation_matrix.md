# Academic Implementation Matrix (HW section → implementation)

| HW section | Implementation | Verification |
|---|---|---|
| HW1 1.2.1 F1 CSV read, map, reject | `src/data/ingestion.py`, `validation.py`, `app/components/upload.py` | `test_ingestion.py`, `test_validation.py`, UX tasks 1–4 |
| HW1 F2 / HW2 5.2 separation of meanings | `src/rules/*`, `configs/financial_rules.yaml` | `test_financial_rules.py`, ledger report |
| HW1 F3 monthly, category, cash flow | `src/analytics/*`, Overview and Analytics pages | `test_aggregation.py`, real-data cross-check, UX task 5 |
| HW1 F4 / HW2 5.3 categories and fallback | `merchant_category`; `ingestion.categorize`, "Uncategorized" | `test_ingestion.py` |
| HW1 F5 / HW2 5.6 budgets | `src/budget/*`, Budget page | `test_budget.py`, UX task 7 |
| HW1 F6 / HW2 5.4 forecasts | `src/models/forecasting/*`, `src/experiments/forecasting_experiment.py` | `test_forecasting.py`, `test_model_loading.py`, E2 |
| HW1 F7 / HW2 5.5 anomaly candidates | `src/models/anomaly/*`, `anomaly_experiment.py` | `test_anomaly.py`, E3, UX task 9 |
| HW1 F8 / HW2 5.7 assistant | `src/assistant/*` | `test_assistant.py`, `test_financial_correctness.py`, UX tasks 10–11 |
| HW1 F9 / HW2 6.5 deletion and privacy | `app/utils/session.py`, `src/utils/logging.py` | `test_csv_upload.py`, UX task 12 |
| HW1 4.4 / HW2 4.4 audit | `scripts/run_audit.py` | `reports/data_audit/*` |
| HW1 4.5 / HW2 4.5 preprocessing | `src/data/preprocessing.py`, `scripts/build_aggregates.py` | `test_preprocessing.py`, preprocessing summary |
| HW1 4.6 / HW2 4.6 leakage | `src/features/*`, `feature_validation.py`, train-only eligibility | `tests/regression/test_data_leakage.py` |
| HW2 6.4 separate training, seed 42, versioned models | `scripts/train_*.py`, `src/utils/reproducibility.py` | `verify_artifacts.py`, `test_reproducibility.py` |
| HW2 8.1–8.5, 10.3 experiments and robustness | `src/experiments/*` | `reports/experiments/*` |
| HW2 9 Tables 9.1/9.2 | `scripts/generate_final_evidence.py` | `reports/final_evidence/results_tables.md` |
| HW2 10.1 validation tests | `tests/unit/test_validation.py`, `test_ingestion.py` | pytest |
