"""Canonical transaction schema shared by the dataset pipeline and user CSV uploads.

The schema is taken from the dataset card (HW1 Table 4.2 / HW2 Table 4.2) and was confirmed
against the actual Parquet schema in reports/verification/dataset_integrity_report.md.
"""
from __future__ import annotations

import polars as pl

from src.utils.configuration import load_config

_CFG = load_config("dataset")

REQUIRED_COLUMNS: list[str] = list(_CFG["expected_columns"])

# Physical types observed in the source Parquet file (verified, not assumed).
SOURCE_DTYPES: dict[str, pl.DataType] = {
    "transaction_id": pl.String,
    "account_id": pl.String,
    "transaction_type": pl.String,
    "amount": pl.Float64,
    "currency": pl.String,
    "merchant_category": pl.String,
    "balance_after": pl.Float64,
    "transaction_timestamp": pl.String,
    "status": pl.String,
}

ALLOWED_CURRENCIES: frozenset[str] = frozenset(_CFG["allowed"]["currencies"])
ALLOWED_STATUSES: frozenset[str] = frozenset(_CFG["allowed"]["statuses"])
KNOWN_TRANSACTION_TYPES: frozenset[str] = frozenset(_CFG["allowed"]["transaction_types"])

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
UNCATEGORIZED = "Uncategorized"

# Columns a user CSV must provide (after mapping). Others have documented defaults.
USER_REQUIRED = ["transaction_timestamp", "amount", "currency"]
USER_OPTIONAL_DEFAULTS = {
    "transaction_id": None,          # generated deterministically if absent
    "account_id": "user-account",
    "transaction_type": None,        # derived from amount sign if absent
    "merchant_category": UNCATEGORIZED,
    "status": None,                  # user must confirm "all completed" if absent
    "balance_after": None,           # never used in calculations
}
