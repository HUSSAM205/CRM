"""Reproducibility: same seed -> identical results; artifacts reload to identical predictions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.experiments import forecasting_experiment as fe
from src.models.forecasting.gradient_boosting import fit_gbr

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/processed/splits/panel_primary.parquet"


def small_panel(seed=0):
    rng = np.random.default_rng(seed)
    return np.round(rng.gamma(0.6, 60, size=(300, 31)) * (rng.random((300, 31)) > 0.45), 2)


def test_gbr_same_seed_identical_predictions():
    Y = small_panel()
    params = {"learning_rate": 0.05, "max_iter": 50, "max_depth": 3, "loss": "absolute_error"}
    tg = list(range(fe.FIRST_TARGET, fe.N_TRAIN))
    from src.features.temporal_features import features_at
    a = fit_gbr(Y, tg, fe.CAL, params, False, 42).predict(features_at(Y, 24, fe.CAL[24]))
    b = fit_gbr(Y, tg, fe.CAL, params, False, 42).predict(features_at(Y, 24, fe.CAL[24]))
    assert np.array_equal(a, b)


@pytest.mark.skipif(not PANEL.exists(), reason="panel not built")
def test_saved_gbr_reproduces_recorded_test_predictions():
    import json

    import joblib
    import polars as pl

    from src.features.temporal_features import features_at
    reg = json.loads((ROOT / "artifacts/metadata/model_registry.json").read_text(encoding="utf-8"))
    model = joblib.load(ROOT / reg["forecasting"]["gbr"]["current"] / "model.joblib")
    keys, Y = fe.load_panel(PANEL)
    t = fe.TEST_COLS[0]
    pred = model.predict(features_at(Y, t, fe.CAL[t]))
    tp = pl.read_parquet(ROOT / "reports/experiments/forecasting/test_predictions.parquet")
    rec = keys.select("account_id", "currency").join(tp.filter(pl.col("month") == "2026-05"),
                                                     on=["account_id", "currency"], how="left")["gbr"].to_numpy()
    assert np.allclose(pred, rec)
