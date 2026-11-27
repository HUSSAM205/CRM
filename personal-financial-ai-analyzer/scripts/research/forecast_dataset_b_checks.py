"""E2-B follow-up checks, run AFTER the gate decision (no change to the frozen decision or model):
  1. Paired bootstrap over users (2,000 resamples, seed 42) of the MAE difference GBR - historical_median, on
     validation and on test: is the improvement distinguishable from zero?
  2. Domain-applicability guard for the product: the model was trained only on continuous series (Dataset B has
     0% zero months). Guard = >= 12 full months AND no zero month in the history. Evaluated on Dataset A test
     cells (read-only): on guarded cells, is GBR-B better than A's historical median? On the others, fallback.
Writes reports/experiments/forecasting_dataset_b/checks.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/research"))
import forecast_dataset_b as E  # noqa: E402


def boot(d: pl.DataFrame, pred: np.ndarray, base: str, n=2000) -> dict:
    t = pl.DataFrame({"u": d["user"], "dg": np.abs(pred - d["y"].to_numpy()), "db": np.abs(d[base].to_numpy() - d["y"].to_numpy())})
    per = t.group_by("u").agg(pl.col("dg").sum(), pl.col("db").sum(), pl.len().alias("n"))
    g, b, n_ = per["dg"].to_numpy(), per["db"].to_numpy(), per["n"].to_numpy()
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(n):
        i = rng.integers(0, len(g), len(g))
        diffs.append((g[i].sum() - b[i].sum()) / n_[i].sum())
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"mae_diff": float((g.sum() - b.sum()) / n_.sum()), "ci95": [float(lo), float(hi)],
            "relative": float((g.sum() - b.sum()) / b.sum()), "users": int(len(g))}


def main() -> None:
    summ = json.loads((E.OUT / "summary.json").read_text())
    model = joblib.load(ROOT / summ["artifact"] / "model.joblib")            # refit on train + validation
    rows = E.build_rows()
    va = rows.filter(pl.col("month").is_between(pl.lit(E.VAL[0]), pl.lit(E.VAL[1])))
    te = rows.filter(pl.col("month").is_between(pl.lit(E.TEST[0]), pl.lit(E.TEST[1])))
    tr = rows.filter(pl.col("month") <= E.TRAIN_END)
    m_tr = E.fit(tr, summ["selected_params"])                                # the validation-time model
    out = {"bootstrap_validation_vs_historical_median": boot(va, E.predict(m_tr, va), "historical_median"),
           "bootstrap_test_vs_historical_median": boot(te, E.predict(model, te), "historical_median")}
    from src.experiments.data_splitting import ALL_MONTHS
    from src.experiments.forecasting_experiment import TEST_COLS, load_panel
    _, Y = load_panel(ROOT / "data/processed/splits/panel_primary.parquet")
    trows = []
    for i in range(Y.shape[0]):
        for r in E.rows_from_series(i, ALL_MONTHS, Y[i]):
            j = ALL_MONTHS.index(r["month"])
            if j in TEST_COLS:
                r["no_zero_history"] = bool((Y[i, :j] != 0).all())
                trows.append(r)
    ta = pl.DataFrame(trows)
    g = ta.filter(pl.col("no_zero_history"))
    out["guard_on_dataset_A_test"] = {
        "cells": ta.height, "guarded_cells": g.height, "guarded_share": g.height / ta.height,
        "guarded": ({"gbr_B": E.metrics(g, E.predict(model, g))["MAE"],
                     "historical_median": E.metrics(g, g["historical_median"].to_numpy())["MAE"],
                     "zero": E.metrics(g, g["zero"].to_numpy())["MAE"]} if g.height else None),
        "product_policy_MAE_on_A": float(np.abs(np.where(ta["no_zero_history"].to_numpy(), E.predict(model, ta),
                                                          ta["historical_median"].to_numpy()) - ta["y"].to_numpy()).mean()),
        "historical_median_only_MAE_on_A": float(np.abs(ta["historical_median"].to_numpy() - ta["y"].to_numpy()).mean())}
    (E.OUT / "checks.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
