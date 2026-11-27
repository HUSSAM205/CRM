"""E2-B: next-month spending forecasting on Dataset B (PersonaLedger normal users; CC BY 4.0; revision c90078ae).
A SEPARATE experiment: it does not change HW2 E2 (Dataset A) or E2-QG.

Pre-registered protocol (fixed in this docstring before any result was produced):
  * Unit: one user (single, unstated currency in the source; never combined with Dataset A amounts).
    Monthly spending = sum of positive amounts (integer cents). Each user's first and last month are partial
    (users start/stop mid-month) and are never used as targets or features.
  * Calendar split by TARGET month: train <= 2026-06, validation 2026-07..2026-12, test 2027-01..2027-06.
    Rolling origin, one month ahead: features use the user's full months before the target only.
  * Eligibility: >= 12 full months of history before the target month (HW2 12-month rule).
  * Deterministic baselines: naive, seasonal_naive, moving_average_3, zero, historical_mean, historical_median,
    rolling_median_6.
  * ML: scale-free HistGradientBoosting (absolute error) on ratios to the user's historical mean
    (lag1..3, rolling mean/median/std 6, history length, calendar month); prediction = ratio x mean.
    Config chosen on validation MAE from 8 configurations (depth 3/6, lr 0.05/0.1, iterations 100/300); seed 42.
  * QUALITY GATE: ACCEPTED only if validation MAE AND MASE are both lower than every deterministic baseline,
    AND test MAE is also lower than the best deterministic baseline on test (no test-based tuning).
  * 80% interval: multiplicative residual quantiles (actual / predicted) on validation in 5 bins of the
    prediction; test coverage reported once.
  * Transfer check: the selected model applied to Dataset A's primary panel (test months), compared with A's
    baselines, to show whether a model learned on B is usable on A.
Outputs: reports/experiments/forecasting_dataset_b/*; artifact only if ACCEPTED.
"""
from __future__ import annotations

import hashlib
import io
import itertools
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "reports/experiments/forecasting_dataset_b"
MONTHLY = ROOT / "data/supplementary/derived/monthly_spend.parquet"
SRC_SHA = "8ec0979c4e578638e81a2665bae9a4a4604675c10cee41578a7377385425ccb5"
TRAIN_END, VAL = "2026-06", ("2026-07", "2026-12")
TEST = ("2027-01", "2027-06")
FEATURES = ["lag1_r", "lag2_r", "lag3_r", "rmean6_r", "rmed6_r", "rstd6_r", "hist_months", "cal_month"]
BASE = ["naive", "seasonal_naive", "moving_average_3", "zero", "historical_mean", "historical_median", "rolling_median_6"]


def all_months(a: str, b: str) -> list[str]:
    y, m = map(int, a.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def rows_from_series(uid, months, y, min_hist=12):
    """One row per eligible target month: features from y[:i] (full months only), target y[i]."""
    out = []
    for i in range(min_hist, len(y)):
        h = y[:i]
        mean = h.mean()
        w = h[-6:]
        scale = np.abs(np.diff(h)).mean() if len(h) > 1 else 0.0
        r = (lambda v: v / mean) if mean > 0 else (lambda v: 0.0 * v)
        out.append({"user": uid, "month": months[i], "y": y[i], "naive": h[-1], "seasonal_naive": h[-12],
                    "moving_average_3": h[-3:].mean(), "zero": 0.0, "historical_mean": mean,
                    "historical_median": float(np.median(h)), "rolling_median_6": float(np.median(w)),
                    "lag1_r": r(h[-1]), "lag2_r": r(h[-2]), "lag3_r": r(h[-3]), "rmean6_r": r(w.mean()),
                    "rmed6_r": r(float(np.median(w))), "rstd6_r": r(w.std()), "hist_months": float(i),
                    "cal_month": float(int(months[i][5:7])), "mase_scale": scale})
    return out


def build_rows() -> pl.DataFrame:
    m = pl.read_parquet(MONTHLY).sort("user_id", "month")
    rows = []
    for (uid,), g in m.group_by(["user_id"], maintain_order=True):
        span = all_months(g["month"][0], g["month"][-1])[1:-1]          # drop partial first and last month
        if len(span) < 13:
            continue
        by = dict(zip(g["month"], g["spend_cents"]))
        y = np.array([by.get(mm, 0) / 100 for mm in span], dtype=float)
        rows += rows_from_series(uid, span, y)
    return pl.DataFrame(rows)


def metrics(d: pl.DataFrame, pred: np.ndarray) -> dict:
    y = d["y"].to_numpy()
    e = pred - y
    per = (pl.DataFrame({"user": d["user"], "ae": np.abs(e), "s": d["mase_scale"]}).filter(pl.col("s") > 0)
             .group_by("user").agg((pl.col("ae").mean() / pl.col("s").first()).alias("m")))
    ss = float(((y - y.mean()) ** 2).sum())
    return {"MAE": float(np.abs(e).mean()), "RMSE": float(np.sqrt((e ** 2).mean())), "MASE": float(per["m"].mean()),
            "R2": 1 - float((e ** 2).sum()) / ss if ss else None, "rows": int(len(y)), "users": int(d["user"].n_unique()),
            "failed_predictions": int((~np.isfinite(pred)).sum()), "zero_prediction_share": float((np.abs(pred) < 0.005).mean())}


def fit(d: pl.DataFrame, p: dict) -> HistGradientBoostingRegressor:
    X = d.select(FEATURES).to_numpy()
    yr = np.where(d["historical_mean"].to_numpy() > 0, d["y"].to_numpy() / np.maximum(d["historical_mean"].to_numpy(), 1e-9), 0.0)
    return HistGradientBoostingRegressor(loss="absolute_error", random_state=42, early_stopping=False, **p).fit(X, yr)


def predict(model, d: pl.DataFrame) -> np.ndarray:
    return model.predict(d.select(FEATURES).to_numpy()) * d["historical_mean"].to_numpy()


def main() -> None:
    t0 = time.time()
    rows = build_rows()
    tr = rows.filter(pl.col("month") <= TRAIN_END)
    va = rows.filter(pl.col("month").is_between(pl.lit(VAL[0]), pl.lit(VAL[1])))
    te = rows.filter(pl.col("month").is_between(pl.lit(TEST[0]), pl.lit(TEST[1])))
    res = {"protocol": __doc__, "dataset_id": "B-PERSONALEDGER-NORMAL", "source_sha256": SRC_SHA,
           "sizes": {"train_rows": tr.height, "train_users": tr["user"].n_unique(), "validation_rows": va.height,
                     "validation_users": va["user"].n_unique(), "test_rows": te.height, "test_users": te["user"].n_unique()},
           "validation": {}, "test": {}}
    for b in BASE:
        res["validation"][b] = metrics(va, va[b].to_numpy())
    grid = []
    for depth, lr, it in itertools.product([3, 6], [0.05, 0.1], [100, 300]):
        p = {"max_depth": depth, "learning_rate": lr, "max_iter": it}
        ts = time.time()
        mdl = fit(tr, p)
        grid.append({**p, **{k: v for k, v in metrics(va, predict(mdl, va)).items() if k in ("MAE", "MASE", "RMSE")},
                     "fit_seconds": round(time.time() - ts, 2)})
    best = min(grid, key=lambda g: (g["MAE"], g["MASE"]))
    params = {k: best[k] for k in ("max_depth", "learning_rate", "max_iter")}
    ts = time.time()
    m_tr = fit(tr, params)
    res["fit_seconds_selected_train"] = round(time.time() - ts, 2)
    pv = predict(m_tr, va)
    res["validation"]["gbr_scale_free"] = metrics(va, pv)
    res["grid"], res["selected_params"] = grid, params
    v = res["validation"]
    best_mae = min(v[b]["MAE"] for b in BASE)
    best_mase = min(v[b]["MASE"] for b in BASE)
    res["best_baseline_validation"] = min(BASE, key=lambda b: v[b]["MAE"])
    passes_val = v["gbr_scale_free"]["MAE"] < best_mae and v["gbr_scale_free"]["MASE"] < best_mase
    # interval: multiplicative residual quantiles on validation
    q = np.quantile(pv, [0.2, 0.4, 0.6, 0.8])
    bins = np.digitize(pv, q)
    ratio = va["y"].to_numpy() / np.maximum(pv, 1e-9)
    iv = {int(b): (float(np.quantile(ratio[bins == b], 0.1)), float(np.quantile(ratio[bins == b], 0.9))) for b in np.unique(bins)}
    res["interval"] = {"edges": q.tolist(), "ratio_quantiles": iv, "level": 0.8,
                       "validation_coverage": float(np.mean([(lo := iv[b][0] * p_) <= y_ <= iv[b][1] * p_ for b, p_, y_ in
                                                             zip(bins, pv, va["y"].to_numpy())]))}
    res["frozen_at_utc"] = datetime.now(timezone.utc).isoformat()
    # ---- test, scored once (refit on train + validation with the frozen config) ----
    trva = pl.concat([tr, va])
    m_final = fit(trva, params)
    for b in BASE:
        res["test"][b] = metrics(te, te[b].to_numpy())
    pt = predict(m_final, te)
    res["test"]["gbr_scale_free"] = metrics(te, pt)
    bt = np.digitize(pt, q)
    yt = te["y"].to_numpy()
    res["interval"]["test_coverage"] = float(np.mean([iv[b][0] * p_ <= y_ <= iv[b][1] * p_ for b, p_, y_ in zip(bt, pt, yt)]))
    best_test = min(BASE, key=lambda b: res["test"][b]["MAE"])
    passes_test = res["test"]["gbr_scale_free"]["MAE"] < res["test"][best_test]["MAE"]
    res["gate"] = {"gbr_scale_free": "ACCEPTED" if passes_val and passes_test else "REJECTED",
                   "passes_validation": passes_val, "passes_test": passes_test, "best_baseline_test": best_test}
    lvl = np.digitize(te["historical_mean"].to_numpy(), np.quantile(te["historical_mean"].to_numpy(), [0.25, 0.5, 0.75]))
    hb = te[res["best_baseline_validation"]].to_numpy()
    res["breakdown_test"] = {
        "by_month": {mm: {"gbr": float(np.abs(pt - yt)[(te["month"] == mm).to_numpy()].mean()),
                          "best_baseline": float(np.abs(hb - yt)[(te["month"] == mm).to_numpy()].mean())}
                     for mm in sorted(te["month"].unique().to_list())},
        "by_spending_quartile": {int(k): {"gbr": float(np.abs(pt - yt)[lvl == k].mean()),
                                          "best_baseline": float(np.abs(hb - yt)[lvl == k].mean())} for k in range(4)},
        "share_users_gbr_better": float((pl.DataFrame({"u": te["user"], "g": np.abs(pt - yt), "b": np.abs(hb - yt)})
                                         .group_by("u").agg((pl.col("g").mean() < pl.col("b").mean()).alias("w")))["w"].mean())}
    # ---- transfer check on Dataset A (primary panel, test months), read-only ----
    from src.experiments.forecasting_experiment import TEST_COLS, load_panel
    _, Y = load_panel(ROOT / "data/processed/splits/panel_primary.parquet")
    trows = []
    from src.experiments.data_splitting import ALL_MONTHS
    for i in range(Y.shape[0]):
        for r in rows_from_series(i, ALL_MONTHS, Y[i]):
            if ALL_MONTHS.index(r["month"]) in TEST_COLS:
                trows.append(r)
    ta = pl.DataFrame(trows)
    res["transfer_to_dataset_A_test"] = {"gbr_scale_free_trained_on_B": metrics(ta, predict(m_final, ta)),
                                         **{b: metrics(ta, ta[b].to_numpy()) for b in ("zero", "historical_median", "moving_average_3")}}
    res["seconds"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(res, indent=1, default=float))
    pl.DataFrame([{"split": s, "model": k, **{m: res[s][k][m] for m in ("MAE", "MASE", "RMSE", "R2", "rows", "users",
                                                                       "zero_prediction_share", "failed_predictions")},
                   "gate": res["gate"].get(k, {}) if isinstance(res["gate"].get(k), str) else
                   ("baseline (best on validation)" if k == res["best_baseline_validation"] else "baseline")}
                  for s in ("validation", "test") for k in res[s]]).write_csv(OUT / "model_comparison.csv")
    if res["gate"]["gbr_scale_free"] == "ACCEPTED":
        ver = "v_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        d = ROOT / "artifacts/forecasting/gbr_personaledger" / ver
        d.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        joblib.dump(m_final, buf)
        (d / "model.joblib").write_bytes(buf.getvalue())
        (d / "feature_schema.json").write_text(json.dumps({"features": FEATURES, "target": "spend / historical_mean",
                                                           "excluded": ["balance_after", "account_id", "transaction_id", "user_id"]}, indent=1))
        meta = {"model_id": "gbr_personaledger", "version": ver, "algorithm": "HistGradientBoostingRegressor (absolute_error)",
                "hyperparameters": params, "random_seed": 42, "dataset_id": "B-PERSONALEDGER-NORMAL", "dataset_sha256": SRC_SHA,
                "dataset_license": "CC BY 4.0 (Capital One Research, PersonaLedger)",
                "training_period": "target months <= 2026-12 (train + validation refit)", "training_rows": trva.height,
                "validation_metrics": v["gbr_scale_free"], "test_metrics": res["test"]["gbr_scale_free"],
                "interval": res["interval"], "gate": res["gate"], "created_at_utc": datetime.now(timezone.utc).isoformat()}
        (d / "metadata.json").write_text(json.dumps(meta, indent=1, default=float))
        (d / "checksum.sha256").write_text(hashlib.sha256((d / "model.joblib").read_bytes()).hexdigest() + "  model.joblib\n")
        res["artifact"] = str(d.relative_to(ROOT))
        (OUT / "summary.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({"sizes": res["sizes"], "params": params, "gate": res["gate"], "seconds": res["seconds"],
                      "artifact": res.get("artifact")}, indent=1))
    for s in ("validation", "test"):
        for k, mm in sorted(res[s].items(), key=lambda x: x[1]["MAE"]):
            print(s, f"{k:20s} MAE {mm['MAE']:.2f} MASE {mm['MASE']:.4f} RMSE {mm['RMSE']:.2f} R2 {mm['R2']:.3f}")
    print("interval", res["interval"]["validation_coverage"], res["interval"]["test_coverage"])
    print("transfer", {k: round(v_["MAE"], 3) for k, v_ in res["transfer_to_dataset_A_test"].items()})


if __name__ == "__main__":
    main()
