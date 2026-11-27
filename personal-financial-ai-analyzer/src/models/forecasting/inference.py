"""Next-month spending estimates for one account-currency series (HW1 F6, HW2 5.4).

Two entry points:
  * outlook_next()  - what the PRODUCT shows (D-22). No ML model passed the E2-QG quality gate (none beat
    the zero-spending baseline on validation), so the app shows the best data-dependent deterministic
    baseline chosen on validation (historical median) with a benchmark-calibrated 80% interval and the
    user's own historical range. Configuration: artifacts/forecasting/outlook/<version>/metadata.json.
  * forecast_next() - the frozen HW2 E2 selection (GBR), kept for the academic record and comparison.
Saved models are only LOADED here, never retrained (HW2 6.4). Series with fewer than 12 active months get
an explicit "not enough data" notice instead of a number.
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
from src.utils.configuration import PROJECT_ROOT, load_config

MIN_ACTIVE_MONTHS = 12


@lru_cache(maxsize=1)
def registry() -> dict:
    p = PROJECT_ROOT / load_config("model_registry")["registry_file"]
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


@lru_cache(maxsize=1)
def outlook_config() -> dict:
    reg = registry().get("forecasting", {}).get("outlook")
    if not reg:
        return {"algorithm": "historical_median", "interval": None, "quality_gate": {}}
    return json.loads((PROJECT_ROOT / reg["current"] / "metadata.json").read_text())


def _benchmark_interval(point: float, cfg: dict) -> tuple[float, float] | None:
    iv = cfg.get("interval")
    if not iv:
        return None
    b = int(np.digitize([point], np.array(iv["edges"]))[0])
    lo, hi = iv["residual_quantiles"][str(b)] if str(b) in iv["residual_quantiles"] else iv["residual_quantiles"][b]
    return point + lo, point + hi


def outlook_next(monthly: pl.DataFrame) -> dict:
    """Product outlook: deterministic historical median of the monthly expenses so far (D-22)."""
    if monthly.is_empty():
        return {"eligible": False, "message": "No completed transactions for this account and currency."}
    months, y, active = series_from_monthly(monthly)
    target = next_month(months[-1])
    if active < MIN_ACTIVE_MONTHS:
        return {"eligible": False, "active_months": active, "target_month": target,
                "message": f"Not enough history for a spending outlook: {active} active month(s); "
                           f"at least {MIN_ACTIVE_MONTHS} are required."}
    cfg = outlook_config()
    point = float(np.median(y))
    iv = _benchmark_interval(point, cfg)
    return {"eligible": True, "active_months": active, "target_month": target, "history_months": len(months),
            "method": cfg.get("algorithm", "historical_median"),
            "point_cents": int(round(point * 100)),
            "benchmark_interval_cents": None if iv is None else (int(round(iv[0] * 100)), int(round(iv[1] * 100))),
            "benchmark_interval_level": None if not cfg.get("interval") else round(cfg["interval"]["level"], 2),
            "benchmark_test_coverage": None if not cfg.get("interval") else cfg["interval"].get("test_coverage"),
            "historical_range_cents": (int(round(float(np.quantile(y, 0.1)) * 100)),
                                       int(round(float(np.quantile(y, 0.9)) * 100))),
            "ml_status": "NOT EFFECTIVE: no ML model beat the zero-spending baseline on validation (E2-QG)",
            "quality_gate": cfg.get("quality_gate", {})}
