"""Forecast accuracy metrics (HW1 1.2.2, HW2 Table 8.2): MAE, RMSE, MASE.

MASE (Hyndman & Koehler 2006): per series, MAE of the forecasts divided by the in-sample MAE of the
one-step naive forecast over that series' TRAINING columns; averaged over series. Series with a
zero scale (constant training history) are excluded from MASE and counted.
"""
from __future__ import annotations

import numpy as np


def mase_scale(Y_train: np.ndarray) -> np.ndarray:
    return np.abs(np.diff(Y_train, axis=1)).mean(axis=1)


def evaluate(actual: np.ndarray, pred: np.ndarray, scale: np.ndarray) -> dict:
    """actual/pred: (n_series, n_months) for the evaluated months."""
    err = pred - actual
    abs_err = np.abs(err)
    ok = scale > 0
    per_series_mase = abs_err[ok].mean(axis=1) / scale[ok]
    return {"MAE": float(abs_err.mean()), "RMSE": float(np.sqrt((err ** 2).mean())),
            "MASE": float(per_series_mase.mean()), "n_series": int(actual.shape[0]),
            "n_months": int(actual.shape[1]), "mase_excluded_zero_scale": int((~ok).sum())}
