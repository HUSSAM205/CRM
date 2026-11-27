"""Post-hoc forecasting error analysis. DIAGNOSTIC ONLY: never used for model selection, which was
frozen on validation data before these numbers existed (DECISIONS D-16).

Questions answered:
  1. How varied are the GBR predictions (could it be acting as a near-constant 'smart median')?
  2. How do simple reference predictors that HW2 does not list compare on the same test cells:
     zero, per-series training median, global training median, per-series training mean?
  3. Where do errors come from: zero-spend months vs active months?
"""
from __future__ import annotations

import numpy as np

from src.evaluation.forecasting_metrics import evaluate, mase_scale


def reference_predictors(Y: np.ndarray, n_hist: int, cols: list[int]) -> dict[str, np.ndarray]:
    hist = Y[:, :n_hist]
    k = len(cols)
    return {"zero": np.zeros((Y.shape[0], k)),
            "series_train_median": np.repeat(np.median(hist, axis=1, keepdims=True), k, axis=1),
            "series_train_mean": np.repeat(hist.mean(axis=1, keepdims=True), k, axis=1),
            "global_train_median": np.full((Y.shape[0], k), float(np.median(hist)))}


def analyse(Y: np.ndarray, preds: dict[str, np.ndarray], cols: list[int], n_train: int, n_hist: int) -> dict:
    scale = mase_scale(Y[:, :n_train])
    actual = Y[:, cols]
    out = {"models": {}, "reference": {}, "prediction_spread": {}, "error_by_month_type": {}}
    for name, p in preds.items():
        out["models"][name] = evaluate(actual, p, scale)
        out["prediction_spread"][name] = {"unique_values": int(np.unique(np.round(p, 2)).size),
                                          "p05": float(np.percentile(p, 5)), "p50": float(np.median(p)),
                                          "p95": float(np.percentile(p, 95)), "std": float(p.std())}
    for name, p in reference_predictors(Y, n_hist, cols).items():
        out["reference"][name] = evaluate(actual, p, scale)
    zero = actual == 0
    out["actual_zero_share"] = float(zero.mean())
    for name, p in {**preds, **reference_predictors(Y, n_hist, cols)}.items():
        e = np.abs(p - actual)
        out["error_by_month_type"][name] = {"MAE_zero_months": float(e[zero].mean()),
                                            "MAE_active_months": float(e[~zero].mean())}
    return out
