"""Forecasting components: baselines, metrics (hand-computed), leakage-safe features, splits."""
from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.forecasting_metrics import evaluate, mase_scale
from src.experiments.data_splitting import (ALL_MONTHS, TEST_MONTHS, TRAIN_MONTHS, VALIDATION_MONTHS,
                                            period_of)
from src.features.temporal_features import features_at
from src.models.forecasting.baselines import moving_average_3, naive, seasonal_naive

Y = np.arange(1, 32, dtype=float).reshape(1, 31) * 10  # 10, 20, ..., 310


def test_split_matches_hw2_table_8_1():
    assert TRAIN_MONTHS[0] == "2024-01" and TRAIN_MONTHS[-1] == "2025-12" and len(TRAIN_MONTHS) == 24
    assert VALIDATION_MONTHS == ["2026-01", "2026-02", "2026-03", "2026-04"]
    assert TEST_MONTHS == ["2026-05", "2026-06", "2026-07"]
    assert ALL_MONTHS == TRAIN_MONTHS + VALIDATION_MONTHS + TEST_MONTHS
    assert [period_of(m) for m in ("2025-12", "2026-01", "2026-05", "2026-08")] == \
        ["train", "validation", "test", "outside"]


def test_baselines_hand_values():
    t = 24  # predict 2026-01 (value 250)
    assert naive(Y, t)[0] == 240
    assert seasonal_naive(Y, t)[0] == 130            # column 12 = 2025-01
    assert moving_average_3(Y, t)[0] == (220 + 230 + 240) / 3
    with pytest.raises(ValueError):
        seasonal_naive(Y, 11)


def test_metrics_hand_values():
    actual = np.array([[10.0, 0.0], [5.0, 5.0]])
    pred = np.array([[8.0, 1.0], [5.0, 9.0]])
    # abs errors 2,1,0,4 -> MAE 1.75 ; squared 4,1,0,16 -> RMSE sqrt(21/4)
    scale = np.array([2.0, 1.0])  # MASE = mean(1.5/2, 2/1) = 1.375
    m = evaluate(actual, pred, scale)
    assert m["MAE"] == pytest.approx(1.75)
    assert m["RMSE"] == pytest.approx(np.sqrt(21 / 4))
    assert m["MASE"] == pytest.approx(1.375)


def test_mase_scale_and_zero_scale_exclusion():
    train = np.array([[1.0, 3.0, 2.0], [4.0, 4.0, 4.0]])
    s = mase_scale(train)
    assert s.tolist() == [1.5, 0.0]
    m = evaluate(np.ones((2, 1)), np.zeros((2, 1)), s)
    assert m["mase_excluded_zero_scale"] == 1 and m["MASE"] == pytest.approx(1 / 1.5)


@pytest.mark.parametrize("seasonal", [False, True])
def test_features_never_use_target_or_future_columns(seasonal):
    rng = np.random.default_rng(0)
    base = rng.normal(size=(5, 31))
    for t in (12, 24, 30):
        f1 = features_at(base, t, 1, seasonal)
        future = base.copy()
        future[:, t:] = 1e9                      # perturb the target and everything after it
        f2 = features_at(future, t, 1, seasonal)
        assert np.array_equal(f1, f2, equal_nan=True)


def test_feature_values():
    f = features_at(Y, 24, 1, seasonal=True)[0]
    assert f.tolist() == [240, 230, 220, np.mean([190, 200, 210, 220, 230, 240]), 1, 130]
