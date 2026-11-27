"""Leakage-safe lag features for monthly series (HW2 5.4, docs/leakage_analysis.md L2).

A panel `Y` has shape (n_series, n_months) and holds monthly expenses in currency units.
The features for target column t use ONLY columns < t.
"""
from __future__ import annotations

import numpy as np

BASE_FEATURES = ["lag_1", "lag_2", "lag_3", "rolling_mean_6", "month"]
SEASONAL_FEATURES = BASE_FEATURES + ["lag_12"]


def features_at(Y: np.ndarray, t: int, calendar_month: int, seasonal: bool = False) -> np.ndarray:
    """Feature matrix (n_series, n_features) for predicting column t from columns < t."""
    if t < 6:
        raise ValueError("need at least 6 prior months for rolling_mean_6")
    n = Y.shape[0]
    cols = [Y[:, t - 1], Y[:, t - 2], Y[:, t - 3], Y[:, t - 6:t].mean(axis=1),
            np.full(n, calendar_month, dtype=float)]
    if seasonal:
        cols.append(Y[:, t - 12] if t >= 12 else np.full(n, np.nan))
    return np.column_stack(cols)


def supervised(Y: np.ndarray, targets: list[int], months: list[int], seasonal: bool = False):
    """Stack (X, y) over target columns. `months[t]` is the calendar month (1-12) of column t."""
    X = np.vstack([features_at(Y, t, months[t], seasonal) for t in targets])
    y = np.concatenate([Y[:, t] for t in targets])
    return X, y
