"""E2-QG: forecasting quality-gate experiment (master audit, separate from the frozen HW2 experiment E2).

Pre-registered protocol (written before any test-period number of this experiment was computed):
  * Same panels, split and rolling origin as E2 (train cols 0-23, validation 24-27, test 28-30).
  * Deterministic baselines: naive, seasonal_naive, moving_average_3 (HW2) plus zero (diagnostic),
    historical_median (expanding median of all prior months), rolling_median_6.
  * ML candidates: the frozen E2 GBR config (base features) and an extended-feature GBR whose config
    is chosen on validation MAE from a 16-point grid.
  * QUALITY GATE: an ML model is ACCEPTED only if its validation MAE AND MASE are both lower than those
    of the best deterministic baseline INCLUDING zero. Otherwise it is REJECTED.
  * PRODUCT OUTLOOK (D-22): zero ignores the user's data, so it is a diagnostic only. The outlook shown
    in the app is the data-dependent deterministic baseline with the lowest validation MAE
    (candidates: naive, seasonal_naive, moving_average_3, historical_median, rolling_median_6), with an
    empirical 80% interval from validation residual quantiles (5 bins of the point forecast).
    Test coverage of that interval is reported, never tuned.
  * Test is scored once, after all choices are frozen and written to the summary.
Outputs: reports/experiments/forecasting_quality_gate/*, reports/figures/research/*,
         artifacts/forecasting/outlook/<version>/metadata.json
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.evaluation.forecasting_metrics import evaluate, mase_scale  # noqa: E402
from src.experiments.forecasting_experiment import CAL, FIRST_TARGET, N_TRAIN, N_VAL, TEST_COLS, VAL_COLS, load_panel  # noqa: E402
from src.features.temporal_features import features_at  # noqa: E402
from src.models.forecasting.baselines import BASELINES  # noqa: E402
from src.models.forecasting.gradient_boosting import fit_gbr  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402

OUT = ROOT / "reports/experiments/forecasting_quality_gate"
FIG = ROOT / "reports/figures/research"
SPLITS = ROOT / "data/processed/splits"
SUMMARY_E2 = json.loads((ROOT / "reports/experiments/forecasting/summary.json").read_text(encoding="utf-8"))


# ---------- deterministic baselines -------------------------------------------------------------
def zero(Y, t):
    return np.zeros(Y.shape[0])


def historical_median(Y, t):
    return np.median(Y[:, :t], axis=1)


def rolling_median_6(Y, t):
    return np.median(Y[:, t - 6:t], axis=1)


DET = {**BASELINES, "zero": zero, "historical_median": historical_median, "rolling_median_6": rolling_median_6}
PRODUCT_CANDIDATES = ["naive", "seasonal_naive", "moving_average_3", "historical_median", "rolling_median_6"]

# ---------- extended features (all from columns < t) --------------------------------------------
EXT_FEATURES = ["lag_1", "lag_2", "lag_3", "rolling_mean_6", "month", "rolling_median_6", "rolling_std_6",
                "zero_share_6", "expanding_mean", "expanding_median", "active_months_so_far"]


def ext_features(Y, t):
    w = Y[:, t - 6:t]
    return np.column_stack([features_at(Y, t, CAL[t]), np.median(w, axis=1), w.std(axis=1), (w == 0).mean(axis=1),
                            Y[:, :t].mean(axis=1), np.median(Y[:, :t], axis=1), (Y[:, :t] != 0).sum(axis=1)])


def fit_ext(Y, targets, params):
    X = np.vstack([ext_features(Y, t) for t in targets])
    y = np.concatenate([Y[:, t] for t in targets])
    return HistGradientBoostingRegressor(random_state=42, early_stopping=False, **params).fit(X, y)


def predict(name, Y, cols, model=None):
    if name in DET:
        return np.column_stack([DET[name](Y, t) for t in cols])
    if name == "gbr_e2":
        return np.column_stack([model.predict(features_at(Y, t, CAL[t])) for t in cols])
    return np.column_stack([model.predict(ext_features(Y, t)) for t in cols])


def metrics(actual, pred, scale):
    m = evaluate(actual, pred, scale)
    e = pred - actual
    ss_tot = float(((actual - actual.mean()) ** 2).sum())
    m.update({"R2": 1 - float((e ** 2).sum()) / ss_tot if ss_tot else None,
              "valid_predictions": int(np.isfinite(pred).sum()), "failed_predictions": int((~np.isfinite(pred)).sum()),
              "zero_prediction_share": float((np.abs(pred) < 0.005).mean()),
              "pred_quantiles": {q: float(np.quantile(pred, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9, 0.99)}})
    return m


def spearman(a, b):
    ra, rb = a.argsort().argsort().astype(float), b.argsort().argsort().astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def interval_model(pred_val, act_val, n_bins=5, lo=0.1, hi=0.9):
    """Residual quantiles per bin of the point forecast (bins from validation forecast quantiles)."""
    edges = np.unique(np.quantile(pred_val, np.linspace(0, 1, n_bins + 1)[1:-1]))
    b = np.digitize(pred_val.ravel(), edges)
    r = (act_val - pred_val).ravel()
    q = {int(i): (float(np.quantile(r[b == i], lo)), float(np.quantile(r[b == i], hi))) for i in np.unique(b)}
    return {"edges": edges.tolist(), "residual_quantiles": q, "level": hi - lo}


def apply_interval(im, pred):
    b = np.digitize(pred, np.array(im["edges"]))
    lo = np.vectorize(lambda i: im["residual_quantiles"][int(i)][0])(b)
    hi = np.vectorize(lambda i: im["residual_quantiles"][int(i)][1])(b)
    return pred + lo, pred + hi


def run_panel(panel: str, full: bool) -> dict:
    keys, Y = load_panel(SPLITS / f"panel_{panel}.parquet")
    scale = mase_scale(Y[:, :N_TRAIN])
    res = {"panel": panel, "series": int(Y.shape[0]), "validation": {}, "test": {}}
    for n in DET:
        res["validation"][n] = metrics(Y[:, VAL_COLS], predict(n, Y, VAL_COLS), scale)
    tr, rf = list(range(FIRST_TARGET, N_TRAIN)), list(range(FIRST_TARGET, N_TRAIN + N_VAL))
    e2p = SUMMARY_E2["primary"]["selected_params"]["gbr"] if "primary" in SUMMARY_E2 else SUMMARY_E2["selected_params"]["gbr"]
    t0 = time.time()
    m_e2 = fit_gbr(Y, tr, CAL, e2p, False)
    res["fit_seconds_gbr_e2"] = round(time.time() - t0, 2)
    res["validation"]["gbr_e2"] = metrics(Y[:, VAL_COLS], predict("gbr_e2", Y, VAL_COLS, m_e2), scale)
    grid = []
    if full:
        G = {"loss": ["absolute_error", "squared_error"], "max_depth": [3, 6], "learning_rate": [0.05, 0.1],
             "max_iter": [100, 300]}
        for vals in itertools.product(*G.values()):
            p = dict(zip(G, vals))
            t0 = time.time()
            m = fit_ext(Y, tr, p)
            met = metrics(Y[:, VAL_COLS], predict("gbr_ext", Y, VAL_COLS, m), scale)
            grid.append({**p, "MAE": met["MAE"], "MASE": met["MASE"], "RMSE": met["RMSE"],
                         "zero_prediction_share": met["zero_prediction_share"], "fit_seconds": round(time.time() - t0, 2)})
        best = min(grid, key=lambda g: (g["MAE"], g["MASE"]))
        res["ext_params"] = {k: best[k] for k in G}
    else:
        res["ext_params"] = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))["primary"]["ext_params"] \
            if (OUT / "summary.json").exists() else None
    res["grid_ext"] = grid
    t0 = time.time()
    m_ext = fit_ext(Y, tr, res["ext_params"])
    res["fit_seconds_gbr_ext"] = round(time.time() - t0, 2)
    res["validation"]["gbr_ext"] = metrics(Y[:, VAL_COLS], predict("gbr_ext", Y, VAL_COLS, m_ext), scale)

    # --- frozen decisions (validation only) ---
    v = res["validation"]
    best_det_mae, best_det_mase = min(v[n]["MAE"] for n in DET), min(v[n]["MASE"] for n in DET)
    res["gate"] = {m: ("ACCEPTED" if v[m]["MAE"] < best_det_mae and v[m]["MASE"] < best_det_mase else "REJECTED")
                   for m in ("gbr_e2", "gbr_ext")}
    res["best_deterministic_by_MAE"] = min(DET, key=lambda n: v[n]["MAE"])
    res["product_outlook"] = min(PRODUCT_CANDIDATES, key=lambda n: (v[n]["MAE"], v[n]["MASE"]))
    pv = predict(res["product_outlook"], Y, VAL_COLS)
    im = interval_model(pv, Y[:, VAL_COLS])
    lo_v, hi_v = apply_interval(im, pv.ravel())
    res["interval"] = {**im, "validation_coverage": float(((Y[:, VAL_COLS].ravel() >= lo_v) & (Y[:, VAL_COLS].ravel() <= hi_v)).mean())}
    res["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()

    # --- test, scored once ---
    for n in DET:
        res["test"][n] = metrics(Y[:, TEST_COLS], predict(n, Y, TEST_COLS), scale)
    res["test"]["gbr_e2"] = metrics(Y[:, TEST_COLS], predict("gbr_e2", Y, TEST_COLS, fit_gbr(Y, rf, CAL, e2p, False)), scale)
    m_ext_rf = fit_ext(Y, rf, res["ext_params"])
    pt_ext = predict("gbr_ext", Y, TEST_COLS, m_ext_rf)
    res["test"]["gbr_ext"] = metrics(Y[:, TEST_COLS], pt_ext, scale)
    pt = predict(res["product_outlook"], Y, TEST_COLS)
    lo_t, hi_t = apply_interval(im, pt.ravel())
    act_t = Y[:, TEST_COLS].ravel()
    res["interval"]["test_coverage"] = float(((act_t >= lo_t) & (act_t <= hi_t)).mean())
    res["interval"]["test_mean_width"] = float((hi_t - lo_t).mean())

    if full:   # diagnostics on the primary panel only
        trainY = Y[:, :N_TRAIN]
        X = np.vstack([ext_features(Y, t) for t in tr])
        yv = np.concatenate([Y[:, t] for t in tr])
        lag1 = [float(np.corrcoef(Y[i, 1:N_TRAIN], Y[i, :N_TRAIN - 1])[0, 1]) for i in range(Y.shape[0])
                if Y[i, :N_TRAIN].std() > 0]
        res["diagnostics"] = {
            "target_train": {"share_zero": float((trainY == 0).mean()), "mean": float(trainY.mean()),
                             "variance": float(trainY.var()), "share_negative": float((trainY < 0).mean()),
                             "quantiles": {q: float(np.quantile(trainY, q)) for q in (0.5, 0.75, 0.9, 0.99)}},
            "target_validation_share_zero": float((Y[:, VAL_COLS] == 0).mean()),
            "target_test_share_zero": float((Y[:, TEST_COLS] == 0).mean()),
            "mean_within_series_lag1_autocorrelation": float(np.nanmean(lag1)),
            "feature_variance": {f: float(X[:, i].var()) for i, f in enumerate(EXT_FEATURES)},
            "feature_target_spearman": {f: spearman(X[:, i], yv) for i, f in enumerate(EXT_FEATURES)},
            "training_examples": int(len(yv)),
            "gbr_e2_feature_set": "lag_1..3, rolling_mean_6, month",
        }
        e = pt_ext - Y[:, TEST_COLS]
        hist_mean = Y[:, :N_TRAIN + N_VAL].mean(axis=1)
        lvl = np.digitize(hist_mean, np.quantile(hist_mean, [0.25, 0.5, 0.75]))
        hl = keys["train_active_months"].to_numpy()
        po = pt - Y[:, TEST_COLS]
        res["breakdowns_test"] = {
            "by_month": {f"col{c}": {"gbr_ext_MAE": float(np.abs(e[:, j]).mean()), "outlook_MAE": float(np.abs(po[:, j]).mean()),
                                     "zero_MAE": float(np.abs(Y[:, c]).mean())} for j, c in enumerate(TEST_COLS)},
            "by_spending_level_quartile": {int(q): {"series": int((lvl == q).sum()),
                                                    "gbr_ext_MAE": float(np.abs(e[lvl == q]).mean()),
                                                    "outlook_MAE": float(np.abs(po[lvl == q]).mean()),
                                                    "zero_MAE": float(np.abs(Y[lvl == q][:, TEST_COLS]).mean())} for q in range(4)},
            "by_history_length": {lab: {"series": int(msk.sum()), "gbr_ext_MAE": float(np.abs(e[msk]).mean()),
                                        "outlook_MAE": float(np.abs(po[msk]).mean()),
                                        "zero_MAE": float(np.abs(Y[msk][:, TEST_COLS]).mean())}
                                  for lab, msk in (("12-13 active months", hl <= 13), ("14-15", (hl >= 14) & (hl <= 15)),
                                                   ("16+", hl >= 16)) if msk.any()},
            "by_currency": {c: {"series": int(msk.sum()), "gbr_ext_MAE": float(np.abs(e[msk]).mean()),
                                "outlook_MAE": float(np.abs(po[msk]).mean())}
                            for c in keys["currency"].unique().to_list()
                            for msk in [keys["currency"].to_numpy() == c]},
            "residual_quantiles_gbr_ext": {q: float(np.quantile(e, q)) for q in (0.01, 0.1, 0.5, 0.9, 0.99)},
        }
        # serialization / reload equality
        import io

        import joblib
        buf = io.BytesIO()
        joblib.dump(m_ext_rf, buf)
        buf.seek(0)
        res["reload_identical_predictions"] = bool(np.array_equal(joblib.load(buf).predict(ext_features(Y, TEST_COLS[0])),
                                                                  m_ext_rf.predict(ext_features(Y, TEST_COLS[0]))))
        res["_plots"] = {"actual_test": Y[:, TEST_COLS].ravel(), "gbr_ext": pt_ext.ravel(),
                         "gbr_e2": predict("gbr_e2", Y, TEST_COLS, fit_gbr(Y, rf, CAL, e2p, False)).ravel(),
                         "outlook": pt.ravel(), "resid": e.ravel()}
    return res


def plots(p: dict) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    out = []
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(-50, 400, 91)
    for k, lab in (("actual_test", "actual"), ("gbr_e2", "GBR (E2)"), ("gbr_ext", "GBR extended"), ("outlook", "outlook baseline")):
        ax.hist(np.clip(p[k], -50, 400), bins=bins, histtype="step", label=lab, density=True)
    ax.set_xlabel("monthly spending (currency units, clipped to [-50, 400])"); ax.set_ylabel("density")
    ax.set_title("Test-period distribution: actual vs predictions"); ax.legend()
    f = FIG / "qg_prediction_distribution.png"; fig.tight_layout(); fig.savefig(f, dpi=120); plt.close(fig); out.append(str(f.relative_to(ROOT)))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(np.clip(p["resid"], -400, 200), bins=120)
    ax.set_xlabel("prediction - actual (GBR extended, test, clipped)"); ax.set_ylabel("cells")
    ax.set_title("Residual distribution")
    f = FIG / "qg_residuals.png"; fig.tight_layout(); fig.savefig(f, dpi=120); plt.close(fig); out.append(str(f.relative_to(ROOT)))
    return out


def main() -> None:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    primary = run_panel("primary", full=True)
    pl_data = primary.pop("_plots")
    (OUT / "summary.json").write_text(json.dumps({"primary": primary}, indent=1, default=float), encoding="utf-8")   # ext_params for robustness
    robust = {p: run_panel(p, full=False) for p in ("seed43", "seed44", "disjoint", "all_eligible")}
    figs = plots(pl_data)
    summary = {"protocol": __doc__, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "seconds": round(time.time() - t0, 1), "primary": primary, "robustness": robust, "figures": figs,
               "e2_reference": {"ets_validation_MAE": SUMMARY_E2.get("primary", SUMMARY_E2).get("validation", {}).get("ets", {}).get("MAE")}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
    rows = []
    for panel, r in [("primary", primary), *robust.items()]:
        for split in ("validation", "test"):
            for model, m in r[split].items():
                rows.append({"panel": panel, "split": split, "model": model, "MAE": m["MAE"], "MASE": m["MASE"],
                             "RMSE": m["RMSE"], "R2": m["R2"], "zero_prediction_share": m["zero_prediction_share"],
                             "valid_predictions": m["valid_predictions"], "failed_predictions": m["failed_predictions"],
                             "series": m["n_series"],
                             "gate_status": r["gate"].get(model, "baseline" if model != r["product_outlook"] else "baseline (product outlook)")})
    pl.DataFrame(rows).write_csv(OUT / "model_comparison.csv")
    if primary["grid_ext"]:
        pl.DataFrame(primary["grid_ext"]).write_csv(OUT / "gbr_ext_grid_validation.csv")
    # product outlook artifact (deterministic: configuration + calibrated interval, no learned weights)
    ver = "v_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta = {"model_id": "forecast_outlook", "version": ver, "algorithm": primary["product_outlook"],
            "type": "deterministic baseline + empirical residual-quantile interval (80%)",
            "hyperparameters": {}, "random_seed": None,
            "dataset_sha256": __import__("yaml").safe_load((ROOT / "configs/dataset.yaml").read_text(encoding="utf-8"))["source"]["expected_sha256"],
            "training_period": "2024-01..2025-12 (none learned)", "calibration_period": "2026-01..2026-04 (validation residuals)",
            "selection": "lowest validation MAE among data-dependent deterministic baselines (D-22)",
            "interval": primary["interval"], "validation_metrics": primary["validation"][primary["product_outlook"]],
            "test_metrics": primary["test"][primary["product_outlook"]], "quality_gate": primary["gate"],
            "created_at_utc": datetime.now(timezone.utc).isoformat()}
    d = ROOT / "artifacts/forecasting/outlook" / ver
    d.mkdir(parents=True, exist_ok=True)
    body = json.dumps(meta, indent=1, default=float)
    (d / "metadata.json").write_text(body, encoding="utf-8")
    (d / "checksum.sha256").write_text(hashlib.sha256(body.encode()).hexdigest() + "  metadata.json\n", encoding="utf-8")
    print(json.dumps({"seconds": summary["seconds"], "gate": primary["gate"], "product_outlook": primary["product_outlook"],
                      "interval": {k: primary["interval"][k] for k in ("validation_coverage", "test_coverage", "test_mean_width")},
                      "artifact": str(d.relative_to(ROOT))}, indent=1))


if __name__ == "__main__":
    main()
