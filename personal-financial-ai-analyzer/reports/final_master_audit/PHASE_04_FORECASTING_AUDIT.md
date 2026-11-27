# Phase 4: Forecasting Audit

Status: **COMPLETE**. The scientific outcome is mixed and is reported as such. Details: `docs/FORECASTING.md` §1–6, `FORECASTING_EXPERIMENTS.md`, `MODEL_COMPARISON.csv`.

| Experiment | Dataset | Best model vs best baseline | Gate |
|---|---|---|---|
| E2 (HW2, frozen) | A | GBR 27.194 vs MA3 39.259 (test MAE) | kept by the HW2 rule (academic record) |
| E2-QG | A | GBR 27.194 / extended GBR 25.374 vs **zero 25.374** | **REJECTED** (both) |
| E2-B | B | scale-free GBR **971.34** vs historical median 1,022.66 (test); bootstrap CI excludes 0 | **ACCEPTED** |
| C3 | C | structured series: GBR 674 vs 781 (validation); i.i.d.: GBR loses | positive control: the pipeline learns when signal exists |

* **Leakage:** E2-B features use only months before the target (`test_E2B_features_use_only_months_before_the_target`). Dataset A L1–L11 pass with data.
* **Product:** domain-guarded routing (D-24). The guard selects 0% of Dataset A cells, so A behaviour is unchanged.
* **Prediction output** carries the amount, currency, target month, model or baseline name, history window, coverage, evidence (metrics), status, 80% range (test coverage stated) and limitations.

The 80% range of E2-B under-covers slightly: 77.7% on test.
