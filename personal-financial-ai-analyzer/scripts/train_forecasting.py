"""Gate 7/9: run the E2 forecasting experiment and save versioned artifacts.

Runs: primary (seed 42 subset, full GBR grid), robustness resamples (seeds 43, 44; frozen configs),
account-disjoint generalization (GBR trained on disjoint accounts, evaluated on primary accounts).
Outputs: reports/experiments/forecasting/*, artifacts/forecasting/<model>/<version>/*
Run inside run_guarded (scripts/run_full_pipeline.py does this) or directly.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import polars as pl
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments import forecasting_experiment as fe  # noqa: E402
from src.experiments.data_splitting import ALL_MONTHS  # noqa: E402
from src.features.temporal_features import BASE_FEATURES, SEASONAL_FEATURES  # noqa: E402
from src.features.feature_validation import assert_allowed  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402
from src.utils.reproducibility import fingerprint, new_artifact_dir, register, set_seed  # noqa: E402

SPLITS = ROOT / "data/processed/splits"
OUT = ROOT / "reports/experiments/forecasting"


def metrics_table(res: dict, run: str) -> list[dict]:
    return [{"run": run, "split": s, "model": m, **{k: v[k] for k in ("MAE", "RMSE", "MASE", "n_series")}}
            for s in ("validation", "test") for m, v in res[s].items()]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config("forecasting")["gbr"]
    seed = load_config("experiments")["seeds"]["primary"]
    set_seed(seed)
    t0 = time.time()
    keys, Y = fe.load_panel(SPLITS / "panel_primary.parquet")
    print(f"primary panel {Y.shape}", flush=True)
    res = fe.run(Y, cfg, seed=seed)
    print(f"primary done {res['seconds']}s selected={res['selected_model']} kept={res['kept_advanced_models']}",
          flush=True)
    rows = metrics_table(res, "primary_seed42")
    pl.DataFrame(res["grid_search"]).write_csv(OUT / "gbr_grid_search_validation.csv")
    pl.DataFrame(fe.per_month(Y, res["preds"]["validation"], fe.VAL_COLS, res["scale"])
                 + fe.per_month(Y, res["preds"]["test"], fe.TEST_COLS, res["scale"])
                 ).write_csv(OUT / "rolling_origin_per_month.csv")
    pl.DataFrame(fe.by_history(keys, Y, res["preds"]["test"], fe.TEST_COLS, res["scale"])
                 ).write_csv(OUT / "test_by_history_length.csv")

    # predictions vs actuals (test, all models) for error analysis / app history
    pred_rows = []
    for j, t in enumerate(fe.TEST_COLS):
        d = {"account_id": keys["account_id"], "currency": keys["currency"],
             "month": [ALL_MONTHS[t]] * len(keys), "actual": Y[:, t]}
        d.update({m: res["preds"]["test"][m][:, j] for m in res["preds"]["test"]})
        pred_rows.append(pl.DataFrame(d))
    pl.concat(pred_rows).write_parquet(OUT / "test_predictions.parquet")

    # robustness resamples: frozen configs, same protocol
    for s in load_config("experiments")["seeds"]["robustness"]:
        if s == seed:
            continue
        _, Ys = fe.load_panel(SPLITS / f"panel_seed{s}.parquet")
        r = fe.run(Ys, cfg, fixed_params=res["selected_params"], seed=s)
        rows += metrics_table(r, f"resample_seed{s}")
        print(f"seed {s} done {r['seconds']}s selected={r['selected_model']}", flush=True)

    # account-disjoint: GBR learns from disjoint accounts, evaluated on primary accounts
    _, Yd = fe.load_panel(SPLITS / "panel_disjoint.parquet")
    rd = fe.run(Y, cfg, fixed_params=res["selected_params"], with_ets=False, gbr_train_Y=Yd, seed=seed)
    rows += [r for r in metrics_table(rd, "account_disjoint_gbr") if r["model"].startswith("gbr")]
    print(f"disjoint done {rd['seconds']}s", flush=True)

    pl.DataFrame(rows).write_csv(OUT / "metrics_all_runs.csv")
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "primary": {"series": int(Y.shape[0]), "validation": res["validation"], "test": res["test"],
                           "best_baseline_by_MAE": res["best_baseline_by_MAE"],
                           "best_baseline_by_MASE": res["best_baseline_by_MASE"],
                           "kept_advanced_models": res["kept_advanced_models"],
                           "selected_model": res["selected_model"],
                           "selected_params": res["selected_params"], "log": res["log"]},
               "total_seconds": round(time.time() - t0, 1),
               "peak_rss_gb_self": round(psutil.Process().memory_info().rss / 1e9, 2),
               "fingerprint": fingerprint()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # Versioned artifacts (never overwrite an existing version)
    for label, feats in (("gbr", BASE_FEATURES), ("gbr_seasonal", SEASONAL_FEATURES)):
        assert_allowed(list(feats))   # leakage guard before saving
        d = new_artifact_dir("forecasting", label, json.dumps(res["selected_params"][label]))
        joblib.dump(res["models"][label], d / "model.joblib")
        (d / "feature_schema.json").write_text(json.dumps({"features": feats, "target": "monthly expenses (currency units)",
                                                            "excluded": ["balance_after", "account_id"]}, indent=2))
        (d / "metrics.json").write_text(json.dumps({"validation": res["validation"][label],
                                                    "test": res["test"][label]}, indent=2))
        (d / "metadata.json").write_text(json.dumps({
            "model": label, "params": res["selected_params"][label], "seed": seed,
            "trained_on": "primary panel, target months 2024-07..2026-04 (train+validation refit)",
            "training_series": int(Y.shape[0]), "training_rows": int(Y.shape[0] * (fe.N_TRAIN + fe.N_VAL - fe.FIRST_TARGET)),
            "selection_status": "kept" if label in res["kept_advanced_models"] else "not kept (did not beat best baseline)",
            "fingerprint": fingerprint()}, indent=2, default=str))
        register("forecasting", label, d, "kept" if label in res["kept_advanced_models"] else "evaluated_not_kept")
    d = new_artifact_dir("forecasting", "selection")
    (d / "metadata.json").write_text(json.dumps({"selected_model": res["selected_model"],
                                                 "rule": load_config("forecasting")["selection_rule"],
                                                 "min_active_train_months": 12,
                                                 "validation": res["validation"]}, indent=2, default=str))
    register("forecasting", "selection", d, "deployed choice")
    print(json.dumps({k: v for k, v in summary["primary"].items() if k not in ("validation", "test")}, indent=2, default=str))


if __name__ == "__main__":
    main()
