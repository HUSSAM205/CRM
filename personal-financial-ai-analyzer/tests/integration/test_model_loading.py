"""The app's inference paths load saved artifacts (never retrain) and handle short histories."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.models.anomaly import anomaly_scoring
from src.models.forecasting import inference

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "artifacts/metadata/model_registry.json"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="no trained artifacts")


def monthly(values: list[int], start=(2024, 1)) -> pl.DataFrame:
    y, m = start
    rows = []
    for v in values:
        rows.append({"month": f"{y:04d}-{m:02d}", "expenses_cents": v, "outflow_cents": max(v, 0), "fee_cents": 0})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return pl.DataFrame(rows)


# 14 months, 13 of them active (>= 12 required); the last month has no spending
ACTIVE_13 = [1000, 500, 2500, 300, 1200, 800, 400, 3000, 1500, 600, 900, 700, 1100, 0]


def test_selection_is_the_validation_choice():
    import json
    meta = json.loads((ROOT / "reports/experiments/forecasting/summary.json").read_text())
    assert inference.selection()["selected_model"] == meta["primary"]["selected_model"]


def test_short_history_gets_notice_not_forecast():
    r = inference.forecast_next(monthly([1000] * 5))
    assert not r["eligible"] and "at least 12" in r["message"]


def test_eligible_history_gets_forecast_from_saved_model():
    r = inference.forecast_next(monthly(ACTIVE_13))
    assert r["eligible"] and r["target_month"] == "2025-03" and isinstance(r["forecast_cents"], int)
    assert r["model"] == inference.selection()["selected_model"]


def test_every_model_path_runs():
    hist = monthly(ACTIVE_13)
    for name in ("naive", "seasonal_naive", "moving_average_3", "gbr", "gbr_seasonal"):
        assert inference.forecast_next(hist, name)["eligible"]
    with pytest.raises(ValueError):
        inference.forecast_next(hist, "ets")         # would need fitting at inference time -> refused


def test_global_forest_loads():
    assert anomaly_scoring.global_forest() is not None


def test_outlook_is_deterministic_median_with_calibrated_interval():
    """E2-QG / D-22: the product outlook is the median of the series, plus the interval from the artifact."""
    import numpy as np
    f = inference.outlook_next(monthly(ACTIVE_13))
    assert f["eligible"] and f["method"] == "historical_median"
    assert f["point_cents"] == int(round(np.median(np.array(ACTIVE_13) / 100) * 100))
    cfg = inference.outlook_config()
    assert cfg["quality_gate"] == {"gbr_e2": "REJECTED", "gbr_ext": "REJECTED"}
    lo, hi = f["benchmark_interval_cents"]
    assert lo <= f["point_cents"] <= hi and f["benchmark_interval_level"] == 0.8
    assert f["historical_range_cents"][0] <= f["point_cents"] <= f["historical_range_cents"][1]
    assert inference.outlook_next(monthly(ACTIVE_13)) == f                          # deterministic


def test_outlook_refuses_short_history():
    f = inference.outlook_next(monthly([1000] * 11))
    assert not f["eligible"] and "at least 12" in f["message"]
