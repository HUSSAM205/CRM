"""Audit: model inventory, step-by-step timed re-execution, independent metric recomputation,
full-eligible-population check, seed-43 investigation. Does NOT write or register any artifact.

Writes reports/audit/training_audit.json
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.evaluation.anomaly_metrics import evaluate as an_eval  # noqa: E402
from src.experiments import forecasting_experiment as fe  # noqa: E402
from src.experiments.anomaly_experiment import run as anomaly_run  # noqa: E402
from src.features.temporal_features import features_at  # noqa: E402
from src.models.forecasting.baselines import BASELINES  # noqa: E402
from src.models.forecasting.ets import ets_forecast  # noqa: E402
from src.models.forecasting.gradient_boosting import fit_gbr, grid  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402

OUT: dict = {"timings_seconds": {}}
T = OUT["timings_seconds"]


def timed(name):
    class _T:
        def __enter__(self):
            self.t = time.perf_counter()

        def __exit__(self, *a):
            T[name] = round(time.perf_counter() - self.t, 3)
    return _T()


def np_metrics(actual, pred, scale):
    """Independent re-implementation (plain numpy) of MAE/RMSE/MASE and extra metrics."""
    e = pred - actual
    ok = scale > 0
    mase = float(np.mean(np.abs(e[ok]).mean(axis=1) / scale[ok]))
    denom = np.abs(actual).sum()
    ss_res, ss_tot = float((e ** 2).sum()), float(((actual - actual.mean()) ** 2).sum())
    nz = actual != 0
    return {"MAE": float(np.abs(e).mean()), "MSE": float((e ** 2).mean()), "RMSE": float(np.sqrt((e ** 2).mean())),
            "MASE": mase, "WAPE": float(np.abs(e).sum() / denom) if denom else None,
            "R2": 1 - ss_res / ss_tot if ss_tot else None,
            "MAPE_nonzero_actuals_only": float(np.mean(np.abs(e[nz] / actual[nz]))) if nz.any() else None,
            "share_actual_zero": float((~nz).mean())}


def tree_stats(m) -> dict:
    if hasattr(m, "_predictors"):          # HistGradientBoostingRegressor
        nodes = [len(t.nodes) for it in m._predictors for t in it]
        leaves = [int(t.nodes["is_leaf"].sum()) for it in m._predictors for t in it]
        return {"type": type(m).__name__, "n_iter": int(m.n_iter_), "trees": len(nodes), "total_nodes": int(sum(nodes)),
                "total_leaves": int(sum(leaves)), "learned_leaf_values": int(sum(leaves)),
                "n_features_in": int(m.n_features_in_), "params": {k: v for k, v in m.get_params().items()
                                                                   if k in ("learning_rate", "max_iter", "max_depth", "loss", "random_state", "early_stopping")}}
    nodes = [e.tree_.node_count for e in m.estimators_]
    return {"type": type(m).__name__, "trees": len(nodes), "total_nodes": int(sum(nodes)),
            "max_samples_per_tree": int(m.max_samples_), "n_features_in": int(m.n_features_in_),
            "params": {k: v for k, v in m.get_params().items() if k in ("n_estimators", "max_samples", "contamination", "random_state")}}


def main() -> None:
    reg = json.loads((ROOT / "artifacts/metadata/model_registry.json").read_text())
    inv = []
    for kind, models in reg.items():
        for name, e in models.items():
            d = ROOT / e["current"]
            rec = {"kind": kind, "model": name, "path": e["current"], "metadata": json.loads((d / "metadata.json").read_text())}
            mf = d / "model.joblib"
            if mf.exists():
                rec["file_bytes"] = mf.stat().st_size
                rec["structure"] = tree_stats(joblib.load(mf))
            inv.append(rec)
    OUT["inventory"] = inv

    # ---------- forecasting: timed re-execution on the primary panel ----------
    cfg = load_config("forecasting")["gbr"]
    summary = json.loads((ROOT / "reports/experiments/forecasting/summary.json").read_text())["primary"]
    with timed("forecast_load_panel"):
        keys, Y = fe.load_panel(ROOT / "data/processed/splits/panel_primary.parquet")
    scale = fe.mase_scale(Y[:, :fe.N_TRAIN])
    tr_targets = list(range(fe.FIRST_TARGET, fe.N_TRAIN))
    OUT["forecast_rows"] = {"series": int(Y.shape[0]), "accounts": int(keys["account_id"].n_unique()),
                            "gbr_train_examples_train_only": int(Y.shape[0] * len(tr_targets)),
                            "gbr_train_examples_refit_train_plus_val": int(Y.shape[0] * (fe.N_TRAIN + fe.N_VAL - fe.FIRST_TARGET)),
                            "validation_cells": int(Y.shape[0] * len(fe.VAL_COLS)), "test_cells": int(Y.shape[0] * len(fe.TEST_COLS)),
                            "ets_fits_per_run": int(Y.shape[0] * (len(fe.VAL_COLS) + len(fe.TEST_COLS)))}
    with timed("forecast_baselines_val"):
        bval = {n: np.column_stack([f(Y, t) for t in fe.VAL_COLS]) for n, f in BASELINES.items()}
    with timed("forecast_ets_val_4_origins"):
        ets_val = np.column_stack([ets_forecast(Y, t)[0] for t in fe.VAL_COLS])
    with timed("forecast_gbr_single_fit_selected"):
        m1 = fit_gbr(Y, tr_targets, fe.CAL, summary["selected_params"]["gbr"], False)
    configs = grid(cfg)
    with timed("forecast_gbr_grid_32_fits_and_val_predictions"):
        for seasonal in (False, True):
            for p in configs:
                m = fit_gbr(Y, tr_targets, fe.CAL, p, seasonal)
                [m.predict(features_at(Y, t, fe.CAL[t], seasonal)) for t in fe.VAL_COLS]
    refit_targets = list(range(fe.FIRST_TARGET, fe.N_TRAIN + fe.N_VAL))
    with timed("forecast_gbr_refit_both_variants"):
        mg = fit_gbr(Y, refit_targets, fe.CAL, summary["selected_params"]["gbr"], False)
        ms = fit_gbr(Y, refit_targets, fe.CAL, summary["selected_params"]["gbr_seasonal"], True)
    with timed("forecast_ets_test_3_origins"):
        ets_test = np.column_stack([ets_forecast(Y, t)[0] for t in fe.TEST_COLS])
    with timed("forecast_serialize_one_model"):
        buf = io.BytesIO()
        joblib.dump(mg, buf)
    # independent metric recomputation vs saved summary
    val_preds = {**bval, "ets": ets_val,
                 "gbr": np.column_stack([m1.predict(features_at(Y, t, fe.CAL[t])) for t in fe.VAL_COLS])}
    test_preds = {n: np.column_stack([f(Y, t) for t in fe.TEST_COLS]) for n, f in BASELINES.items()}
    test_preds.update(ets=ets_test, gbr=np.column_stack([mg.predict(features_at(Y, t, fe.CAL[t])) for t in fe.TEST_COLS]),
                      gbr_seasonal=np.column_stack([ms.predict(features_at(Y, t, fe.CAL[t], True)) for t in fe.TEST_COLS]))
    hist = Y[:, :fe.N_TRAIN + fe.N_VAL]
    k = len(fe.TEST_COLS)
    test_preds.update(zero=np.zeros((Y.shape[0], k)),
                      historical_mean=np.repeat(hist.mean(1, keepdims=True), k, 1),
                      historical_median=np.repeat(np.median(hist, 1, keepdims=True), k, 1))
    repro = []
    for split, preds, cols in (("validation", val_preds, fe.VAL_COLS), ("test", test_preds, fe.TEST_COLS)):
        for name, p in preds.items():
            mm = np_metrics(Y[:, cols], p, scale)
            saved = summary[split].get(name)
            repro.append({"split": split, "model": name, **mm,
                          "saved_MAE": saved["MAE"] if saved else None,
                          "abs_diff_MAE": abs(mm["MAE"] - saved["MAE"]) if saved else None,
                          "abs_diff_MASE": abs(mm["MASE"] - saved["MASE"]) if saved else None})
    OUT["forecast_reproduction"] = repro
    gb = test_preds["gbr"]
    OUT["gbr_prediction_profile_test"] = {"unique_values": int(np.unique(np.round(gb, 4)).size),
                                          "share_exactly_zero": float((gb == 0).mean()),
                                          "share_below_1_unit": float((np.abs(gb) < 1).mean())}
    # per-series MAE distribution and per-currency
    per_series = {n: np.abs(test_preds[n] - Y[:, fe.TEST_COLS]).mean(1) for n in ("gbr", "zero", "moving_average_3")}
    OUT["per_series_test_MAE_quantiles"] = {n: {q: float(np.quantile(v, q)) for q in (0.1, 0.5, 0.9, 0.99)}
                                            for n, v in per_series.items()}
    OUT["share_series_gbr_better_than_zero"] = float((per_series["gbr"] < per_series["zero"]).mean())
    cur = keys["currency"].to_numpy()
    OUT["per_currency_test_MAE"] = {c: {n: float(per_series[n][cur == c].mean()) for n in per_series}
                                    | {"series": int((cur == c).sum())} for c in np.unique(cur)}

    # ---------- seed-43 identical-results investigation ----------
    _, Y43 = fe.load_panel(ROOT / "data/processed/splits/panel_seed43.parquet")
    a = fit_gbr(Y43, refit_targets, fe.CAL, summary["selected_params"]["gbr"], False, 43)
    b = fit_gbr(Y43, refit_targets, fe.CAL, summary["selected_params"]["gbr_seasonal"], True, 43)
    pa_ = np.concatenate([a.predict(features_at(Y43, t, fe.CAL[t])) for t in fe.TEST_COLS])
    pb_ = np.concatenate([b.predict(features_at(Y43, t, fe.CAL[t], True)) for t in fe.TEST_COLS])
    rng = np.random.default_rng(0)
    Xr = np.column_stack([rng.gamma(0.6, 60, (5000, 4)), rng.integers(1, 13, 5000), rng.gamma(0.6, 60, 5000)])
    OUT["seed43_investigation"] = {
        "test_predictions_identical": bool(np.array_equal(pa_, pb_)),
        "unique_pred_values_gbr": int(np.unique(pa_).size), "unique_pred_values_gbr_seasonal": int(np.unique(pb_).size),
        "share_zero_pred_gbr": float((pa_ == 0).mean()),
        "random_inputs_identical": bool(np.array_equal(a.predict(Xr[:, :5]), b.predict(Xr))),
        "seasonal_model_split_features": sorted({int(f) for it in b._predictors for t in it
                                                 for f in t.nodes["feature_idx"][t.nodes["is_leaf"] == 0]}),
    }

    # ---------- full eligible population (GBR + baselines + references; ETS omitted for cost) ----------
    full_p = ROOT / "data/processed/splits/panel_all_eligible.parquet"
    if full_p.exists():
        with timed("full_population_load"):
            kf, Yf = fe.load_panel(full_p)
        sf = fe.mase_scale(Yf[:, :fe.N_TRAIN])
        with timed("full_population_gbr_fit_train_only"):
            mf_ = fit_gbr(Yf, tr_targets, fe.CAL, summary["selected_params"]["gbr"], False)
        with timed("full_population_gbr_refit"):
            mr_ = fit_gbr(Yf, refit_targets, fe.CAL, summary["selected_params"]["gbr"], False)
        res = {}
        hf = Yf[:, :fe.N_TRAIN + fe.N_VAL]
        for split, cols, model, h in (("validation", fe.VAL_COLS, mf_, Yf[:, :fe.N_TRAIN]), ("test", fe.TEST_COLS, mr_, hf)):
            kk = len(cols)
            preds = {n: np.column_stack([f(Yf, t) for t in cols]) for n, f in BASELINES.items()}
            preds.update(gbr=np.column_stack([model.predict(features_at(Yf, t, fe.CAL[t])) for t in cols]),
                         zero=np.zeros((Yf.shape[0], kk)), historical_median=np.repeat(np.median(h, 1, keepdims=True), kk, 1),
                         historical_mean=np.repeat(h.mean(1, keepdims=True), kk, 1))
            res[split] = {n: np_metrics(Yf[:, cols], p, sf) for n, p in preds.items()}
        OUT["full_eligible_population"] = {"series": int(Yf.shape[0]), "gbr_train_examples": int(Yf.shape[0] * len(tr_targets)),
                                           "gbr_refit_examples": int(Yf.shape[0] * len(refit_targets)), "metrics": res}

    # ---------- anomaly: timed re-execution and metric comparison ----------
    exp, acfg = load_config("experiments"), load_config("anomaly_detection")
    tx = pl.read_parquet(ROOT / "data/processed/splits/anomaly_transactions.parquet")
    with timed("anomaly_full_experiment_9_runs"):
        r = anomaly_run(tx, exp["anomaly"]["injection_rates"], exp["seeds"]["robustness"], acfg["isolation_forest"], 42)
    saved = pl.read_csv(ROOT / "reports/experiments/anomaly/metrics_all_runs.csv")
    new = pl.DataFrame(r["results"])
    j = saved.join(new, on=["rate", "seed", "model"], suffix="_new")
    OUT["anomaly_reproduction"] = {"rows_compared": j.height,
                                   "max_abs_diff_roc_auc": float((j["roc_auc"] - j["roc_auc_new"]).abs().max()),
                                   "max_abs_diff_precision_at_k": float((j["precision_at_k"] - j["precision_at_k_new"]).abs().max()),
                                   "history_rows": r["history_rows"], "scored_rows": r["scored_rows"],
                                   "per_account_forests_fitted_and_discarded": int(tx["account_id"].n_unique()),
                                   "experiment_seconds_internal": r["seconds"]}
    # F1 / FPR at k from the saved primary scores (independent of the experiment code)
    ps = pl.read_parquet(ROOT / "reports/experiments/anomaly/primary_scores.parquet")
    y = ps["y"].to_numpy()
    f1 = {}
    for col in ("score_robust_z", "score_if_per_account", "score_if_global"):
        s = ps[col].to_numpy()
        kpos = int(y.sum())
        top = np.zeros(len(y), bool)
        top[np.argsort(-s, kind="stable")[:kpos]] = True
        tp = int((top & (y == 1)).sum())
        fp = int((top & (y == 0)).sum())
        prec, rec = tp / kpos, tp / kpos
        f1[col] = {"k": kpos, "tp": tp, "fp": fp, "precision": prec, "recall": rec,
                   "f1": 2 * prec * rec / (prec + rec) if tp else 0.0, "false_positive_rate": fp / int((y == 0).sum()),
                   **{m: an_eval(y, s)[m] for m in ("roc_auc", "average_precision")}}
    OUT["anomaly_threshold_at_k_from_saved_scores"] = f1
    (ROOT / "reports/audit/training_audit.json").write_text(json.dumps(OUT, indent=2, default=str))
    print(json.dumps(T, indent=1))


if __name__ == "__main__":
    main()
