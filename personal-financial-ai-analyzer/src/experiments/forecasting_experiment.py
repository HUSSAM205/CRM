"""E2 forecasting experiment (HW2 5.4, 8.2, 8.3, 10.3).

Protocol
  * Panel Y (n_series x 31 months, currency units). Columns 0-23 train, 24-27 validation, 28-30 test.
  * Rolling origin, one month ahead: the forecast for column t uses columns < t only.
  * Validation: baselines; ETS refit per origin; GBR trained on train-period targets (columns 6..23)
    for every grid configuration. GBR config chosen on validation MAE.
  * Decision (HW2 5.4): an advanced model is KEPT only if its validation MAE AND MASE are both lower
    than the best baseline's (best per metric). Test months are not used for any choice.
  * Test: GBR refit on columns 6..27 with the frozen config; ETS refit per origin; scored once.
"""
from __future__ import annotations

import time

import numpy as np
import polars as pl

from src.evaluation.forecasting_metrics import evaluate, mase_scale
from src.experiments.data_splitting import ALL_MONTHS, TEST_MONTHS, TRAIN_MONTHS, VALIDATION_MONTHS
from src.features.temporal_features import features_at
from src.models.forecasting.baselines import BASELINES
from src.models.forecasting.ets import ets_forecast
from src.models.forecasting.gradient_boosting import fit_gbr, grid

N_TRAIN, N_VAL = len(TRAIN_MONTHS), len(VALIDATION_MONTHS)
VAL_COLS = list(range(N_TRAIN, N_TRAIN + N_VAL))
TEST_COLS = list(range(N_TRAIN + N_VAL, len(ALL_MONTHS)))
CAL = [int(m[5:7]) for m in ALL_MONTHS]
FIRST_TARGET = 6  # rolling_mean_6 needs 6 prior months


def load_panel(path) -> tuple[pl.DataFrame, np.ndarray]:
    df = pl.read_parquet(path)
    Y = df.select(ALL_MONTHS).to_numpy().astype(float) / 100.0   # cents -> currency units
    return df.select("account_id", "currency", "train_active_months"), Y


def predict_cols(model_name: str, Y: np.ndarray, cols: list[int], gbr=None, seasonal=False,
                 log: dict | None = None) -> np.ndarray:
    preds = []
    for t in cols:
        if model_name in BASELINES:
            preds.append(BASELINES[model_name](Y, t))
        elif model_name == "ets":
            p, w = ets_forecast(Y, t)
            if log is not None:
                log["ets_warnings"] = log.get("ets_warnings", 0) + w
            preds.append(p)
        else:
            preds.append(gbr.predict(features_at(Y, t, CAL[t], seasonal)))
    return np.column_stack(preds)


def run(Y: np.ndarray, gbr_cfg: dict, fixed_params: dict | None = None, with_ets: bool = True,
        gbr_train_Y: np.ndarray | None = None, seed: int = 42) -> dict:
    """Run validation + test. `gbr_train_Y` lets GBR learn from a different (disjoint) panel."""
    t0 = time.time()
    scale = mase_scale(Y[:, :N_TRAIN])
    log: dict = {}
    out: dict = {"validation": {}, "test": {}, "preds": {"validation": {}, "test": {}}, "log": log}
    trainY = Y if gbr_train_Y is None else gbr_train_Y
    train_targets = list(range(FIRST_TARGET, N_TRAIN))

    names = list(BASELINES) + (["ets"] if with_ets else [])
    for name in names:
        p = predict_cols(name, Y, VAL_COLS, log=log)
        out["preds"]["validation"][name] = p
        out["validation"][name] = evaluate(Y[:, VAL_COLS], p, scale)

    # GBR: grid search on validation (or a fixed config for robustness runs)
    search = []
    for seasonal, label in ((False, "gbr"), (True, "gbr_seasonal")):
        configs = [fixed_params[label]] if fixed_params else grid(gbr_cfg)
        best = None
        for params in configs:
            m = fit_gbr(trainY, train_targets, CAL, params, seasonal, random_state=seed)
            p = predict_cols(label, Y, VAL_COLS, gbr=m, seasonal=seasonal)
            met = evaluate(Y[:, VAL_COLS], p, scale)
            search.append({"model": label, **params, **{k: met[k] for k in ("MAE", "RMSE", "MASE")}})
            if best is None or (met["MAE"], met["MASE"]) < (best[1]["MAE"], best[1]["MASE"]):
                best = (params, met, p)
        out["validation"][label] = best[1]
        out["preds"]["validation"][label] = best[2]
        out.setdefault("selected_params", {})[label] = best[0]
    out["grid_search"] = search

    # Decision rule on validation only
    base = {k: v for k, v in out["validation"].items() if k in BASELINES}
    best_mae = min(v["MAE"] for v in base.values())
    best_mase = min(v["MASE"] for v in base.values())
    out["best_baseline_by_MAE"] = min(base, key=lambda k: base[k]["MAE"])
    out["best_baseline_by_MASE"] = min(base, key=lambda k: base[k]["MASE"])
    kept = {k: v for k, v in out["validation"].items()
            if k not in BASELINES and v["MAE"] < best_mae and v["MASE"] < best_mase}
    out["kept_advanced_models"] = sorted(kept)
    out["selected_model"] = (min(kept, key=lambda k: kept[k]["MAE"]) if kept
                             else out["best_baseline_by_MAE"])

    # Test: refit on train+validation with frozen choices, score once
    refit_targets = list(range(FIRST_TARGET, N_TRAIN + N_VAL))
    out["models"] = {}
    for name in names:
        p = predict_cols(name, Y, TEST_COLS, log=log)
        out["preds"]["test"][name] = p
        out["test"][name] = evaluate(Y[:, TEST_COLS], p, scale)
    for seasonal, label in ((False, "gbr"), (True, "gbr_seasonal")):
        m = fit_gbr(trainY, refit_targets, CAL, out["selected_params"][label], seasonal, random_state=seed)
        out["models"][label] = m
        p = predict_cols(label, Y, TEST_COLS, gbr=m, seasonal=seasonal)
        out["preds"]["test"][label] = p
        out["test"][label] = evaluate(Y[:, TEST_COLS], p, scale)
    out["scale"] = scale
    out["seconds"] = round(time.time() - t0, 1)
    return out


def per_month(Y: np.ndarray, preds: dict, cols: list[int], scale: np.ndarray) -> list[dict]:
    rows = []
    for name, p in preds.items():
        for j, t in enumerate(cols):
            met = evaluate(Y[:, [t]], p[:, [j]], scale)
            rows.append({"model": name, "month": ALL_MONTHS[t], "MAE": met["MAE"], "RMSE": met["RMSE"],
                         "MASE": met["MASE"]})
    return rows


def by_history(keys: pl.DataFrame, Y: np.ndarray, preds: dict, cols: list[int], scale: np.ndarray) -> list[dict]:
    """HW2 10.3: short vs long histories evaluated separately."""
    act = keys["train_active_months"].to_numpy()
    groups = {"short (12-13 active train months)": act <= 13, "long (>=14 active train months)": act >= 14}
    rows = []
    for g, mask in groups.items():
        for name, p in preds.items():
            met = evaluate(Y[mask][:, cols], p[mask], scale[mask])
            rows.append({"history": g, "model": name, "n_series": int(mask.sum()),
                         **{k: met[k] for k in ("MAE", "RMSE", "MASE")}})
    return rows
