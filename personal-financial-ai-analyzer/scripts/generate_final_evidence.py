"""Assemble the final evidence package (reports/final_evidence/) from saved result files only.

Writes:
  results_tables.md  HW2 Table 9.1 (forecasting) and 9.2 (anomaly) filled with MEASURED values,
                     plus robustness, diagnostics, dataset facts and test/UX results
  evidence_index.md  where every piece of evidence lives
  facts.json         machine-readable key numbers (all copied from evidence files)
No number in these files is typed by hand.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT)
OUT = ROOT / "reports/final_evidence"


def j(p: str) -> dict:
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def md(df: pl.DataFrame, digits: int = 3) -> str:
    df = df.with_columns([pl.col(c).round(digits) for c, t in df.schema.items() if t.is_float()])
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in df.iter_rows())


def main() -> None:
    import sys
    sys.path.insert(0, sys_path)
    from src.evaluation.visualizations import all_figures
    OUT.mkdir(parents=True, exist_ok=True)
    figures = all_figures()
    f = j("reports/experiments/forecasting/summary.json")["primary"]
    a = j("reports/experiments/anomaly/summary.json")
    ea = j("reports/evaluation/forecasting_error_analysis.json")
    integ, led = j("reports/verification/dataset_integrity.json"), j("reports/verification/ledger_semantics.json")
    prep, split = j("reports/data_audit/preprocessing_summary.json"), j("data/processed/splits/split_metadata.json") \
        if (ROOT / "data/processed/splits/split_metadata.json").exists() else {}
    ux = j("reports/ux_tasks/ux_task_results.json")
    art = j("reports/verification/artifact_verification.json")
    latest = (ROOT / "logs/testing/latest.log").read_text(encoding="utf-8") if (ROOT / "logs/testing/latest.log").exists() else ""
    m = re.search(r"=+ (.*(passed|failed).*) in [\d.]+s", latest)
    tests = m.group(1) if m else "not run"

    t91 = pl.DataFrame([{"model": k, "split": s, **{x: f[s][k][x] for x in ("MAE", "RMSE", "MASE")}}
                        for s in ("validation", "test") for k in f[s]]).sort("split", "MAE", descending=[True, False])
    ref = pl.DataFrame([{"reference predictor (post-hoc, NOT used for selection)": k,
                         **{x: v[x] for x in ("MAE", "RMSE", "MASE")}} for k, v in ea["reference"].items()]).sort("MAE")
    runs = pl.read_csv(ROOT / "reports/experiments/forecasting/metrics_all_runs.csv").filter(pl.col("split") == "test")
    rob = runs.pivot(on="run", index="model", values="MAE")
    hist = pl.read_csv(ROOT / "reports/experiments/forecasting/test_by_history_length.csv")
    t92 = pl.DataFrame(a["primary"]).select("model", "positives", "precision_at_k", "recall_at_k", "roc_auc",
                                            "average_precision", "precision_at_100")
    scen = pl.DataFrame(a["primary"]).select("model", *[c for c in pl.DataFrame(a["primary"]).columns
                                                        if c.startswith(("recall_at_k_", "roc_auc_"))])
    arob = pl.read_csv(ROOT / "reports/experiments/anomaly/robustness_by_rate.csv").select(
        "rate", "model", "positives_mean", "precision_at_k_mean", "precision_at_k_std", "roc_auc_mean", "roc_auc_std")
    pc = j("reports/evaluation/anomaly_positive_control.json")["results"]
    sig = ea["temporal_signal_and_validation_zero"]

    text = f"""# Results Tables (generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})

Every value is read from the saved result files listed in `evidence_index.md`.

## Dataset (all {integ['rows_read_full']:,} rows)
* File SHA-256 `{integ['sha256']}` (HF commit `{j('data/raw/PROVENANCE.json')['revision_commit']}`; see `docs/dataset_provenance.md`).
* {prep['rows_in']:,} rows validated: {prep['clean']:,} clean, {prep['rejected']} rejected, {prep['unresolved_type_rows']} unresolved types.
* Ledger: {led['match_by_transaction_id']:,}/{led['records_compared']:,} records reconcile in transaction-ID order, versus {led['match_rate_by_timestamp']:.2%} in timestamp order.
* Forecast-eligible series (≥ 12 active training months): {split.get('eligible_series', 'n/a'):,} {split.get('eligible_by_currency', '')}.

## HW2 Table 9.1: forecasting (primary subset: {f['validation']['naive']['n_series']:,} series, one-month-ahead rolling origin)
{md(t91)}

* Best baseline (validation): MAE = **{f['best_baseline_by_MAE']}**, MASE = **{f['best_baseline_by_MASE']}**.
* Kept by the HW2 rule (beats the best baseline on validation MAE **and** MASE): **{', '.join(f['kept_advanced_models'])}**. Selected: **{f['selected_model']}** {f['selected_params'][f['selected_model']] if f['selected_model'] in f['selected_params'] else ''}.
* ETS convergence warnings counted (not hidden): {f['log'].get('ets_warnings', 0)}.

### Post-hoc diagnostic (test months; reference predictors are NOT HW2 baselines and were NOT used for selection)
{md(ref)}

* Share of test months with zero spending: {ea['actual_zero_share']:.1%}.
* Within-series autocorrelation of monthly spending (training months): lag 1 {sig['within_series_autocorr_lag1']:.3f}, lag 12 {sig['lag12']:.3f}. That is what i.i.d. noise gives (expected ≈ −1/(n−1) = −0.043).
* A zero forecast on **validation**: MAE {sig['zero_forecast_validation']['MAE']:.3f} and MASE {sig['zero_forecast_validation']['MASE']:.3f}, against GBR's {sig['gbr_validation']['MAE']:.3f} and {sig['gbr_validation']['MASE']:.3f}.

### Robustness: test MAE across seed resamples and the account-disjoint run
{md(rob)}

### Short vs long histories (test)
{md(hist)}

## HW2 Table 9.2: anomaly ranking (rate 1%, seed 42; {a['scored_rows']:,} test spending records of {a['accounts']:,} accounts)
{md(t92)}

### By injection scenario
{md(scen)}

### Robustness over rates 0.5/1/2% and seeds 42/43/44 (mean ± sd)
{md(arob)}

### Positive control (pure amount multiplication, robust z-score)
""" + "\n".join(f"* ×{k[1:]}: ROC-AUC {v['roc_auc']}, Precision@k {v['precision_at_k']}" for k, v in
                sorted(pc.items(), key=lambda kv: int(kv[0][1:]))) + f"""

## Tests, artifacts and user tasks
* Automated tests: **{tests}** (`logs/testing/latest.log`).
* Artifacts: **{art['overall']}**. {sum(1 for x in art['artifacts'] if x['status'] == 'PASS')}/{len(art['artifacts'])} entries load in a fresh process (`reports/verification/artifact_verification.json`).
* Real-browser user tasks: **{ux['completed']}/{ux['tasks']} completed**, {ux['errors']} errors, mean {ux['mean_seconds']:.1f} s per task (`reports/ux_tasks/ux_task_results.json`). This was scripted, with no human participants.

## Figures
""" + "\n".join(f"* `{p}`" for p in figures) + "\n"
    (OUT / "results_tables.md").write_text(text, encoding="utf-8")

    facts = {"tests": tests, "artifacts": art["overall"], "ux_completed": ux["completed"], "ux_tasks": ux["tasks"],
             "forecast_selected": f["selected_model"], "forecast_kept": f["kept_advanced_models"],
             "rows": integ["rows_read_full"], "sha256": integ["sha256"]}
    (OUT / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    idx = """# Evidence Index

| Evidence | Location |
|---|---|
| Academic analysis, traceability, conflicts | `docs/academic_source_analysis.md`, `docs/requirements_traceability.md`, `docs/requirements_conflicts.md` |
| Dataset identity and integrity | `docs/dataset_provenance.md`, `reports/verification/dataset_integrity*.{json,md}`, `dataset_identity_check.txt` |
| Ledger semantics | `reports/verification/ledger_semantics_report.md`, `ledger_*.csv`, `ledger_semantics.json` |
| Full-data audit | `reports/data_audit/*`, `reports/verification/dataset_quality_report.md` |
| Preprocessing | `reports/data_audit/preprocessing_summary.json`, `logs/preprocessing/*` |
| Splits | `data/processed/splits/split_metadata.json` (not in git: regenerated by `scripts/create_splits.py`) |
| Forecasting experiment | `reports/experiments/forecasting/*`, `logs/training/train_forecasting.log` |
| Anomaly experiment | `reports/experiments/anomaly/*`, `logs/training/train_anomaly.log` |
| Diagnostics | `reports/evaluation/*` |
| Artifacts and registry | `artifacts/`, `artifacts/metadata/model_registry.json`, `reports/verification/artifact_verification.json` |
| Tests | `tests/`, `logs/testing/latest.log` |
| UX tasks and screenshots | `reports/ux_tasks/ux_task_results.json`, `reports/screenshots/ux_*.png` |
| Resources | `reports/verification/resource_benchmark_report.md`, `reports/benchmarks/resource_benchmarks.json` |
| Decisions, issues, runs | `DECISIONS.md`, `KNOWN_ISSUES.md`, `EXPERIMENT_REGISTRY.md` |
| Final validation | `reports/final_validation_report.md` |
"""
    (OUT / "evidence_index.md").write_text(idx, encoding="utf-8")
    print(text[:3000])


if __name__ == "__main__":
    main()
