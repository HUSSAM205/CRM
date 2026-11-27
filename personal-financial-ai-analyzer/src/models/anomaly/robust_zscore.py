"""Robust z-score baseline (HW2 5.5): median/MAD of the account's history of log(amount).

z = 0.6745 * (log_amount - median) / MAD ; score = |z| (higher = more unusual).
MAD = 0 (all history amounts equal) uses MAD := 1e-6 so any deviation scores very high; this is
counted in the experiment output. Accounts without history get score 0 (no evidence).
Needs no training, so the app computes it directly from a user's own history.
"""
from __future__ import annotations

import polars as pl

MAD_FLOOR = 1e-6


def robust_z_expr() -> pl.Expr:
    mad = pl.when(pl.col("acc_log_mad") > 0).then(pl.col("acc_log_mad")).otherwise(MAD_FLOOR)
    z = 0.6745 * (pl.col("amount").log() - pl.col("acc_log_median")) / mad
    return z.abs().fill_null(0.0).alias("score_robust_z")
