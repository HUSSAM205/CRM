"""Anomaly ranking metrics (HW2 Table 8.2): Precision@k, recall, ROC-AUC (+ average precision)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def precision_recall_at_k(y: np.ndarray, score: np.ndarray, k: int) -> tuple[float, float]:
    order = np.argsort(-score, kind="stable")[:k]
    hits = y[order].sum()
    return float(hits / k), float(hits / max(1, y.sum()))


def evaluate(y: np.ndarray, score: np.ndarray, scenario: np.ndarray | None = None) -> dict:
    k = int(y.sum())  # D-10: k = number of injected positives
    p_k, r_k = precision_recall_at_k(y, score, k)
    out = {"n": int(len(y)), "positives": k, "precision_at_k": p_k, "recall_at_k": r_k,
           "precision_at_50": precision_recall_at_k(y, score, 50)[0],
           "precision_at_100": precision_recall_at_k(y, score, 100)[0],
           "roc_auc": float(roc_auc_score(y, score)), "average_precision": float(average_precision_score(y, score))}
    if scenario is not None:
        top = np.zeros(len(y), bool)
        top[np.argsort(-score, kind="stable")[:k]] = True
        for s in np.unique(scenario[y == 1]):
            m = (scenario == s) & (y == 1)
            out[f"recall_at_k_{s}"] = float(top[m].mean())
            neg = y == 0
            out[f"roc_auc_{s}"] = float(roc_auc_score(np.r_[np.ones(m.sum()), np.zeros(neg.sum())],
                                                      np.r_[score[m], score[neg]]))
    return out
