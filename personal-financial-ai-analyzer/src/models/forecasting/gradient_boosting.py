"""Gradient boosting regressor on lag features (HW2 5.4).

Implementation: scikit-learn HistGradientBoostingRegressor (a gradient-boosting regressor that also
handles the NaN lag_12 of the seasonal ablation natively). Fitted on training-period targets only.
"""
from __future__ import annotations

import itertools

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from src.features.temporal_features import supervised


def grid(cfg: dict) -> list[dict]:
    keys = list(cfg["grid"])
    return [dict(zip(keys, vals)) for vals in itertools.product(*(cfg["grid"][k] for k in keys))]


def fit_gbr(Y: np.ndarray, targets: list[int], months: list[int], params: dict, seasonal: bool,
            random_state: int = 42) -> HistGradientBoostingRegressor:
    X, y = supervised(Y, targets, months, seasonal)
    model = HistGradientBoostingRegressor(random_state=random_state, early_stopping=False, **params)
    return model.fit(X, y)
