"""Exponential smoothing ETS(A,N,N) per series (HW2 5.4), refit at every forecast origin.

A series with only two seasons of training data cannot support a reliable seasonal ETS, so the
non-seasonal additive-error form is used (configs/forecasting.yaml). Convergence warnings are
COUNTED and reported, never silenced.
"""
from __future__ import annotations

import warnings

import numpy as np
from joblib import Parallel, delayed
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def _one(y: np.ndarray) -> tuple[float, int]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            fit = ExponentialSmoothing(y, trend=None, seasonal=None,
                                       initialization_method="estimated").fit()
            pred = float(fit.forecast(1)[0])
            if not np.isfinite(pred):
                raise ValueError("non-finite forecast")
        except Exception:
            pred, caught = float(y[-1]), [*caught, "fit_failed_fallback_naive"]
    return pred, len(caught)


def ets_forecast(Y: np.ndarray, t: int, n_jobs: int = 4) -> tuple[np.ndarray, int]:
    """One-step forecast of column t from columns < t, per row. Returns (predictions, n_warnings)."""
    out = Parallel(n_jobs=n_jobs, batch_size=256)(delayed(_one)(Y[i, :t]) for i in range(Y.shape[0]))
    preds = np.array([p for p, _ in out])
    return preds, int(sum(w for _, w in out))
