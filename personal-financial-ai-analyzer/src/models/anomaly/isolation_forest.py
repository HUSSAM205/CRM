"""Isolation Forest (Liu et al. 2008; HW1 3.1.2, HW2 5.5) in two variants (DECISIONS D-07).

per-account : one forest per account, fitted on that account's history only (HW2 5.5 primary).
global      : one forest fitted on account-relative features of many accounts' history; this is the
              saved artifact the app loads (HW2 6.4: the app does not retrain).
Score = -score_samples (higher = more anomalous).
"""
from __future__ import annotations

import numpy as np
from joblib import Parallel, delayed
from sklearn.ensemble import IsolationForest


def make_forest(cfg: dict, seed: int) -> IsolationForest:
    return IsolationForest(n_estimators=cfg["n_estimators"], max_samples=cfg["max_samples"],
                           contamination=cfg["contamination"], random_state=seed)


def fit_global(X_hist: np.ndarray, cfg: dict, seed: int) -> IsolationForest:
    return make_forest(cfg, seed).fit(X_hist)


def _per_account_chunk(items: list, cfg: dict, seed: int) -> list:
    out = []
    for acc_id, Xh, Xs in items:
        if len(Xh) < 2 or len(Xs) == 0:
            out.append((acc_id, np.zeros(len(Xs)), False))   # not enough history: no evidence
            continue
        f = make_forest(cfg, seed).fit(Xh)
        out.append((acc_id, -f.score_samples(Xs), True))
    return out


def score_per_account(groups: list[tuple[str, np.ndarray, np.ndarray]], cfg: dict, seed: int,
                      n_jobs: int = 4) -> dict[str, tuple[np.ndarray, bool]]:
    """groups: (account_id, history_X, rows_to_score_X). Forests are discarded after scoring."""
    chunks = [groups[i::n_jobs * 8] for i in range(n_jobs * 8)]
    res = Parallel(n_jobs=n_jobs)(delayed(_per_account_chunk)(c, cfg, seed) for c in chunks if c)
    return {a: (s, fitted) for chunk in res for a, s, fitted in chunk}
