# Personal Financial AI Analyzer & Advisor

Academic prototype by **Hussam Aburahmah (2357138)**, for Special Topics in Artificial Intelligence Engineering 1, Bahçeşehir University.

It turns a bank-style CSV into reliable financial summaries (**Analyzer**) and evidence-based budgeting, savings, what-if and affordability guidance (**Advisor**). Money totals are **deterministic**, computed in integer cents and kept per currency. Machine learning was evaluated for **forecasting next-month spending** and **ranking unusual transactions for review**, following HW1's hybrid design and HW2's methodology. Forecasting ML did **not** pass the quality gate on this synthetic data, so the app shows a transparent deterministic outlook instead (`docs/FORECASTING.md`).

> Educational prototype. It is not a bank, an investment, credit or tax advisor, or a fraud service. Unusual transactions are *review recommendations*, not fraud findings.

## Quick start (Windows)

```bat
setup.bat
```

```bat
run.bat
```

Then open http://localhost:8501, go to **Transactions**, and choose **Load demo data** or upload a CSV. The trained models are included, so the dataset is not needed to run the app. Details: `docs/installation_guide.md`, `docs/USER_GUIDE.md`.

To reproduce everything from the 50M-row dataset (resumable and memory-guarded for a 16 GB laptop), then run the read-only audit:

```bat
train.bat
```

```bat
audit.bat
```

Windows status: **not tested on Windows** (`docs/WINDOWS_INSTALLATION.md`).

## What is verified

The independent master audit is in `reports/final_master_audit/` (start with `EXECUTIVE_SUMMARY.md`).

| Area | Result | Evidence |
|---|---|---|
| Dataset identity | HF commit `98cf38f9…`, SHA-256 matches the official LFS hash, 50,000,000 rows | `reports/final_master_audit/DATASET_FORENSIC_REPORT.md` |
| Financial correctness | Full-data reconciliation 9,488/9,488 exact; curated fixtures exact | `reports/final_master_audit/FINANCIAL_RECONCILIATION.md` |
| Forecasting | HW2 rule keeps GBR, but the quality gate **rejects** it (a zero forecast is better); the product shows the historical-median outlook with a calibrated 80% interval (test coverage 81.9%) | `docs/FORECASTING.md` |
| Unusual transactions | AUC 0.56–0.59, F1 ≤ 0.041 at about 1% FPR: weak; shown as review recommendations only | `docs/ANOMALY_DETECTION.md` |
| Advisor | goals, what-if, affordability, ranked recommendations with known-answer tests | `docs/ADVISOR.md` |
| Tests and browser workflows | see the latest results | `reports/final_master_audit/TEST_RESULTS.md`, `BROWSER_TEST_RESULTS.md` |

## Layout

`app/` Streamlit dashboard (8 sections) · `src/` core library (data, rules, analytics, features, models, experiments, evaluation, assistant, budget, advisor, utils) · `scripts/` pipeline steps · `configs/` YAML settings · `tests/` unit, integration and regression tests · `docs/` documentation · `reports/` evidence · `artifacts/` versioned models.

Architecture: `docs/ARCHITECTURE.md`. Decisions: `DECISIONS.md`. Status: `PROJECT_STATUS.md`. Limitations: `docs/KNOWN_LIMITATIONS.md`.

## Data and license

Dataset: [ziadatalabs/FreeFinancialTransactions50M](https://huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M), fully synthetic, **CC BY-NC 4.0**, created by Zia Data Labs. It is used here non-commercially, with attribution. The raw data is not stored in git.
