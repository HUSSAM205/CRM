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


def test_artifact_verification_runs_without_derived_data(tmp_path):
    """Master audit M-06: in a fresh clone (no dataset) every saved model must still load in a fresh process
    and predict on real rows; the verifier falls back to the committed demo sample."""
    import json
    import os
    import subprocess
    import sys
    env = {**os.environ, "ARTIFACT_VERIFY_INPUT": "demo", "ARTIFACT_VERIFY_OUT": str(tmp_path / "v.json")}
    r = subprocess.run([sys.executable, "scripts/verify_artifacts.py"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    out = json.loads((tmp_path / "v.json").read_text())
    loaded = [a for a in out["artifacts"] if a["fresh_process_load"] is True]
    with_model = [a for a in out["artifacts"] if (ROOT / a["path"] / "model.joblib").exists()]
    assert len(loaded) == len(with_model) >= 3                      # every saved model loaded (count from the registry)
    assert all(a["detail"]["input"].startswith("demo") for a in loaded)


def test_scale_free_features_match_experiment():
    """D-24: the app's feature code must equal the E2-B experiment's feature code exactly."""
    import sys

    import numpy as np
    sys.path.insert(0, str(ROOT / "scripts/research"))
    import forecast_dataset_b as E

    from src.models.forecasting import scale_free
    rng = np.random.default_rng(0)
    months = [f"{2024 + i // 12}-{i % 12 + 1:02d}" for i in range(20)]
    for y in (rng.gamma(2.0, 500.0, 20), np.r_[np.zeros(3), rng.gamma(2.0, 50.0, 17)]):
        rows = E.rows_from_series(0, months, y)
        for r in rows:
            i = months.index(r["month"])
            x, mean = scale_free.features(y[:i], r["month"])
            assert np.allclose(x[0], [r[f] for f in scale_free.FEATURES]) and mean == r["historical_mean"]


def test_forecast_product_routes_by_training_domain():
    """Continuous history -> accepted E2-B model; intermittent history -> deterministic outlook; short -> none."""
    reg = inference.registry()["forecasting"]
    if "gbr_personaledger" not in reg:
        pytest.skip("E2-B artifact not registered")
    cont = inference.forecast_product(monthly([300000 + (i % 5) * 20000 for i in range(20)]))
    assert cont["method"] == "gbr_personaledger" and cont["model_status"].startswith("ACCEPTED")
    lo, hi = cont["interval_cents"]
    assert lo < cont["point_cents"] < hi and "best baseline" in cont["evidence"]
    inter = inference.forecast_product(monthly(ACTIVE_13))                      # contains a zero month
    assert inter["method"] == "historical_median" and "without spending" in inter["domain_check"]
    assert inter["point_cents"] == inference.outlook_next(monthly(ACTIVE_13))["point_cents"]
    assert not inference.forecast_product(monthly([1000] * 8))["eligible"]
