# Personal Financial AI Analyzer

Academic prototype by **Hussam Aburahmah (2357138)**, for Special Topics in Artificial Intelligence Engineering 1, Bahçeşehir University.

It turns a bank-style CSV into reliable financial summaries. Money totals are **deterministic**, computed in integer cents and kept per currency. Machine learning is used only to **forecast next-month spending** and to **rank unusual transactions for review**, following the hybrid design of HW1 and the methodology of HW2.

> Educational prototype. It is not a bank, an investment advisor or a fraud service. Anomalies are *review candidates*, not fraud findings.

## Quick start (Windows)

```bat
setup.bat
```

```bat
run.bat
```

Then open http://localhost:8501, go to **Transactions**, and choose **Load demo data** or upload a CSV. The trained models are included, so the dataset is not needed to run the app. Details: `docs/installation_guide.md`, `docs/user_guide.md`.

To reproduce everything from the 50M-row dataset (resumable and memory-guarded for a 16 GB laptop):

```bat
train.bat
```

## What is verified

| Area | Result | Evidence |
|---|---|---|
| Dataset identity | HF commit `98cf38f9…`, SHA-256 matches the official LFS hash, 50,000,000 rows | `docs/dataset_provenance.md` |
| Ledger semantics | 49,000,000/49,000,000 records reconcile in ID order; sign convention measured | `reports/verification/ledger_semantics_report.md` |
| Full audit and preprocessing | All 50M rows: 0 rejected, 0 missing, 0 duplicates | `reports/data_audit/` |
| Financial correctness | Hand fixtures; 0 mismatches against an independent `Decimal` recomputation | `reports/verification/financial_rules_validation.md` |
| Forecasting (HW2 E2) | GBR selected by HW2's rule. **Caveat:** a zero forecast is as good or better, because the synthetic series carry no temporal signal | `docs/final_results.md` |
| Anomaly ranking (HW2 E3) | Amount anomalies detectable (AUC up to 0.80); hour and category at chance; positive control AUC 0.999 | `reports/final_evidence/results_tables.md` |
| Tests | 118 automated tests pass | `logs/testing/latest.log` |
| Real-browser tasks | 12/12 | `reports/ux_tasks/ux_task_results.json` |
| Final acceptance | See report | `reports/final_validation_report.md` |

## Layout

`app/` Streamlit dashboard · `src/` core library (data, rules, analytics, features, models, experiments, evaluation, assistant, budget, utils) · `scripts/` pipeline steps · `configs/` YAML settings · `tests/` unit, integration and regression tests · `docs/` documentation · `reports/` evidence · `artifacts/` versioned models.

Architecture: `docs/architecture.md`. Decisions: `DECISIONS.md`. Status: `PROJECT_STATUS.md`. Limitations: `docs/limitations.md`.

## Data and license

Dataset: [ziadatalabs/FreeFinancialTransactions50M](https://huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M), fully synthetic, **CC BY-NC 4.0**, created by Zia Data Labs. It is used here non-commercially, with attribution. The raw data is not stored in git.
