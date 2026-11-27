"""Next-month spending forecast for one account-currency series (HW1 F6, HW2 5.4).

Uses the model chosen by the validation decision rule (artifacts/metadata/model_registry.json ->
forecasting/selection). Saved models are only LOADED here, never retrained (HW2 6.4).
Series with fewer than 12 active months get an explicit "not enough data" notice instead.
"""
from __future__ import annotations

import json
from functools import lru_cache

import joblib
import numpy as np
import polars as pl

from src.experiments.data_splitting import month_range
from src.features.temporal_features import features_at
from src.models.forecasting.baselines import BASELINES
from src.utils.configuration import PROJECT_ROOT

MIN_ACTIVE_MONTHS = 12


@lru_cache(maxsize=1)
def registry() -> dict:
    p = PROJECT_ROOT / "artifacts/metadata/model_registry.json"
    return json.loads(p.read_text()) if p.exists() else {}


@lru_cache(maxsize=1)
def selection() -> dict:
    reg = registry().get("forecasting", {}).get("selection")
    if not reg:
        return {"selected_model": "naive", "note": "no trained selection found; naive baseline used"}
    return json.loads((PROJECT_ROOT / reg["current"] / "metadata.json").read_text())


@lru_cache(maxsize=4)
def load_model(name: str):
    reg = registry()["forecasting"][name]
    return joblib.load(PROJECT_ROOT / reg["current"] / "model.joblib")


def next_month(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y + (m == 12):04d}-{1 if m == 12 else m + 1:02d}"


def series_from_monthly(monthly: pl.DataFrame) -> tuple[list[str], np.ndarray, int]:
    """monthly: one account-currency's rows of src.analytics.financial_metrics.monthly_summary."""
    months = month_range(monthly["month"].min(), monthly["month"].max())
    by = {r["month"]: r for r in monthly.iter_rows(named=True)}
    y = np.array([by[m]["expenses_cents"] / 100 if m in by else 0.0 for m in months])
    active = sum(1 for m in months if m in by and (by[m]["outflow_cents"] + by[m]["fee_cents"]) > 0)
    return months, y, active


def forecast_next(monthly: pl.DataFrame, model: str | None = None) -> dict:
    if monthly.is_empty():
        return {"eligible": False, "message": "No completed transactions for this account and currency."}
    months, y, active = series_from_monthly(monthly)
    target = next_month(months[-1])
    if active < MIN_ACTIVE_MONTHS:
        return {"eligible": False, "active_months": active, "target_month": target,
                "message": f"Not enough history for a forecast: {active} active month(s); "
                           f"at least {MIN_ACTIVE_MONTHS} are required."}
    name = model or selection()["selected_model"]
    Y = y.reshape(1, -1)
    t = Y.shape[1]
    if name in BASELINES:
        if name == "seasonal_naive" and t < 12:
            name = "naive"
        pred = float(BASELINES[name](Y, t)[0])
    elif name in ("gbr", "gbr_seasonal"):
        pred = float(load_model(name).predict(features_at(Y, t, int(target[5:7]), name == "gbr_seasonal"))[0])
    else:
        raise ValueError(f"model '{name}' cannot be used for inference without retraining")
    return {"eligible": True, "active_months": active, "target_month": target, "model": name,
            "forecast_cents": int(round(pred * 100)), "history_months": len(months)}
