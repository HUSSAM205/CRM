# Personal Financial AI Analyzer & Advisor

Four cooperating pillars: **Analyzer** (what happened), **Advisor** (what you could do next), **Predictive Intelligence** (only where evaluation justifies it) and a **local Assistant** (no external AI service or API key).

Academic prototype by **Hussam Aburahmah (2357138)**, for Special Topics in Artificial Intelligence Engineering 1, Bahçeşehir University.

It turns a bank-style CSV into reliable financial summaries (**Analyzer**) and evidence-based budgeting, savings, what-if and affordability guidance (**Advisor**). Money totals are **deterministic**, computed in integer cents and kept per currency. Machine learning was evaluated for **forecasting next-month spending** and **ranking unusual transactions for review**, following HW1's hybrid design and HW2's methodology. Forecasting ML did **not** pass the quality gate on this synthetic data, so the app shows a transparent deterministic outlook instead (`docs/FORECASTING.md`).

> Educational prototype. It is not a bank, an investment, credit or tax advisor, or a fraud service. Unusual transactions are *review recommendations*, not fraud findings.

## Quick start (Windows)

1. Install **Python 3.12 (64-bit)** from python.org and tick "Add python.exe to PATH".
2. Double-click **`START_HERE.bat`**. The first run installs the packages; every run starts the app and opens **http://localhost:8501**. The app is local-only and works offline after setup.
3. To stop the app, close the black window or double-click **`STOP.bat`**.

Then try the app with **Transactions › Load demo data**, or follow the practical walkthrough with two synthetic bank exports in `docs/DEMO_WALKTHROUGH.md`.
* Later files can be **added** to the loaded data: duplicates are skipped and reported.
* Replacing the data needs an explicit confirmation.
* The trained models are included, so the 1.6 GB dataset is not needed to run the app.

Details: `docs/WINDOWS_INSTALLATION.md`. First-run checklist: `docs/WINDOWS_LAPTOP_VERIFICATION.md`.

To reproduce everything from the 50M-row dataset (resumable and memory-guarded for a 16 GB laptop), then run the read-only audit:

```bat
train.bat
```

```bat
audit.bat
```

Windows status: prepared and statically checked; **not yet executed on Windows** (`docs/WINDOWS_LAPTOP_VERIFICATION.md`).

## What is verified

The latest delivery report (master audit 4, Windows delivery) is `reports/master_audit_4/DELIVERY_REPORT.md`; the last full audit is `reports/master_audit_3/FINAL_MASTER_AUDIT.md`. Earlier audits are in `reports/final_master_audit/` and `reports/final_audit/`.

| Area | Result | Evidence |
|---|---|---|
| Dataset identity | HF commit `98cf38f9…`, SHA-256 matches the official LFS hash, 50,000,000 rows | `reports/final_master_audit/DATASET_FORENSIC_REPORT.md` |
| Financial correctness | Full-data reconciliation 9,488/9,488 exact; curated fixtures exact | `reports/final_master_audit/FINANCIAL_RECONCILIATION.md` |
| Forecasting | Dataset A (HW2 E2): the HW2 rule **kept** GBR (it beats the HW2 baselines). A later, post-hoc check (E2-QG) found that a zero forecast is better, so the product does not rely on it. Dataset B (PersonaLedger, CC BY 4.0, supplementary): a scale-free GBR passed its gate (test MAE −5.0% vs the best baseline; user-level bootstrap CI excludes 0). The product uses it only for continuous series and otherwise falls back to the historical-median outlook | `docs/FORECASTING.md` |
| Datasets | A = original academic benchmark (unchanged); B = supplementary public data; C = controlled synthetic tests | `docs/DATASET_REGISTRY.md` |
| Unusual transactions | AUC 0.56–0.59, F1 ≤ 0.041 at about 1% FPR: weak; shown as review recommendations only | `docs/ANOMALY_DETECTION.md` |
| Advisor | goals, what-if, affordability, ranked recommendations with known-answer tests | `docs/ADVISOR.md` |
| Tests and browser workflows | see the latest results | `reports/master_audit_4/DELIVERY_REPORT.md` |

## Layout

`app/` Streamlit dashboard (8 sections) · `src/` core library (data, rules, analytics, features, models, experiments, evaluation, assistant, budget, advisor, utils) · `scripts/` pipeline steps · `configs/` YAML settings · `tests/` unit, integration and regression tests · `docs/` documentation · `reports/` evidence · `artifacts/` versioned models.

Guides: `docs/ANALYZER_GUIDE.md`, `docs/ADVISOR_GUIDE.md`, `docs/ASSISTANT_GUIDE.md`, `docs/SECURITY.md`, `docs/PRIVACY.md`. Architecture: `docs/ARCHITECTURE.md`. Decisions: `DECISIONS.md`. Status: `PROJECT_STATUS.md`. Limitations: `docs/KNOWN_LIMITATIONS.md`.

## Data and license

Dataset: [ziadatalabs/FreeFinancialTransactions50M](https://huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M), fully synthetic, **CC BY-NC 4.0**, created by Zia Data Labs. It is used here non-commercially, with attribution. The raw data is not stored in git.
