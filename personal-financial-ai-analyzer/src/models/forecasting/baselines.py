"""Forecasting baselines (HW2 5.4): one-step-ahead predictions for column t of panel Y."""
from __future__ import annotations

import numpy as np


def naive(Y: np.ndarray, t: int) -> np.ndarray:
    """Last month's value."""
    return Y[:, t - 1].copy()


def seasonal_naive(Y: np.ndarray, t: int) -> np.ndarray:
    """Same month of the previous year."""
    if t < 12:
        raise ValueError("seasonal naive needs 12 prior months")
    return Y[:, t - 12].copy()


def moving_average_3(Y: np.ndarray, t: int) -> np.ndarray:
    """Mean of the three previous months."""
    return Y[:, t - 3:t].mean(axis=1)


BASELINES = {"naive": naive, "seasonal_naive": seasonal_naive, "moving_average_3": moving_average_3}
