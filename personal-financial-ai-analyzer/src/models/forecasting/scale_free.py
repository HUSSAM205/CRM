"""Scale-free next-month spending features (experiment E2-B, Dataset B / PersonaLedger, D-24).

Identical to scripts/research/forecast_dataset_b.py::rows_from_series (pinned by
tests/integration/test_model_loading.py::test_scale_free_features_match_experiment). Features are ratios to
the series' historical mean, so the model is independent of the currency's magnitude.
"""
from __future__ import annotations

import numpy as np

FEATURES = ["lag1_r", "lag2_r", "lag3_r", "rmean6_r", "rmed6_r", "rstd6_r", "hist_months", "cal_month"]
MIN_HISTORY = 12


def features(history: np.ndarray, target_month: str) -> tuple[np.ndarray, float]:
    """Feature row for predicting the month after `history` (monthly amounts in currency units)."""
    h = np.asarray(history, dtype=float)
    mean = h.mean()
    w = h[-6:]
    r = (lambda v: v / mean) if mean > 0 else (lambda v: 0.0 * v)
    x = [r(h[-1]), r(h[-2]), r(h[-3]), r(w.mean()), r(float(np.median(w))), r(w.std()), float(len(h)),
         float(int(target_month[5:7]))]
    return np.array([x]), float(mean)


def in_domain(history: np.ndarray) -> tuple[bool, str]:
    """Domain guard: the model was trained only on continuous series (no month without spending, >= 12 months)."""
    h = np.asarray(history, dtype=float)
    if len(h) < MIN_HISTORY:
        return False, f"fewer than {MIN_HISTORY} months of history"
    if (h <= 0).any():
        return False, "your history contains months without spending (outside the model's training data)"
    return True, "continuous monthly history like the model's training data"
