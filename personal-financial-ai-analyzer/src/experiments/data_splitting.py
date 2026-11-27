"""Chronological split definitions (HW2 Table 8.1) and month utilities.

Periods come from configs/experiments.yaml; they were verified to equal the data's month coverage
(reports/verification/methodology_feasibility.json, check M1).
"""
from __future__ import annotations

import polars as pl

from src.utils.configuration import load_config

_SPLIT = load_config("experiments")["split"]
TRAIN = tuple(_SPLIT["train"])
VALIDATION = tuple(_SPLIT["validation"])
TEST = tuple(_SPLIT["test"])


def month_range(start: str, end: str) -> list[str]:
    out, (y, m) = [], map(int, start.split("-"))
    while f"{y:04d}-{m:02d}" <= end:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


ALL_MONTHS = month_range(TRAIN[0], TEST[1])
TRAIN_MONTHS = month_range(*TRAIN)
VALIDATION_MONTHS = month_range(*VALIDATION)
TEST_MONTHS = month_range(*TEST)


def period_of(month: str) -> str:
    if TRAIN[0] <= month <= TRAIN[1]:
        return "train"
    if VALIDATION[0] <= month <= VALIDATION[1]:
        return "validation"
    if TEST[0] <= month <= TEST[1]:
        return "test"
    return "outside"


def period_expr(col: str = "month") -> pl.Expr:
    m = pl.col(col)
    return (pl.when((m >= TRAIN[0]) & (m <= TRAIN[1])).then(pl.lit("train"))
              .when((m >= VALIDATION[0]) & (m <= VALIDATION[1])).then(pl.lit("validation"))
              .when((m >= TEST[0]) & (m <= TEST[1])).then(pl.lit("test"))
              .otherwise(pl.lit("outside")))


def month_index(month: str) -> int:
    """0-based position of `month` in ALL_MONTHS."""
    return ALL_MONTHS.index(month)
