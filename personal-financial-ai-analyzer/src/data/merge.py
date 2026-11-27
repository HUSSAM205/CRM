"""Explicit append/import of a further validated file into the loaded transactions (master audit 3, MA3-01).

* Existing records are never modified or dropped.
* A new record whose (account_id, transaction_id) is already loaded is NOT added. It is listed among the
  rejected rows with reason ``already_loaded``, so nothing disappears silently.
* A file whose bytes were already imported in this session is refused as a whole.
* The combined total range is checked again (int64-cent exactness, audit M-02).

Replacement is a separate operation (``app.utils.session.set_data``) that the user must confirm in the UI.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import polars as pl

from src.data.validation import CORE_REQUIRED, TotalOutOfRangeError, check_total_range

KEY = ["account_id", "transaction_id"]


class DuplicateImportError(ValueError):
    """The same file (identical bytes) was already imported in this session."""


@dataclass
class MergeResult:
    clean: pl.DataFrame
    rejected: pl.DataFrame
    added: int
    already_loaded: int
    rejected_in_file: int


def file_fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _with_source(rejected: pl.DataFrame, label: str) -> pl.DataFrame:
    if "source_file" in rejected.columns:
        return rejected
    return rejected.with_columns(pl.lit(label).alias("source_file"))


def _clean_as_rejected(rows: pl.DataFrame, reason: str) -> pl.DataFrame:
    """Express clean rows in the rejected-frame schema (values as strings, original row number kept)."""
    return rows.select(
        pl.col("source_row"),
        *[(pl.col(c).dt.strftime("%Y-%m-%d %H:%M:%S") if c == "transaction_timestamp" else pl.col(c).cast(pl.String))
          .alias(c) for c in CORE_REQUIRED],
        pl.lit(reason).alias("reject_reason"))


def merge(existing_clean: pl.DataFrame, existing_rejected: pl.DataFrame, existing_label: str,
          new_clean: pl.DataFrame, new_rejected: pl.DataFrame, new_label: str) -> MergeResult:
    """Append `new_clean` to `existing_clean`, skipping records that are already loaded."""
    dup_mask = new_clean.select(pl.struct(KEY).is_in(existing_clean.select(pl.struct(KEY)).to_series().implode())).to_series()
    dups, fresh = new_clean.filter(dup_mask), new_clean.filter(~dup_mask)
    clean = pl.concat([existing_clean, fresh], how="vertical")
    try:
        check_total_range(clean)
    except TotalOutOfRangeError as e:
        raise TotalOutOfRangeError(f"combined with the loaded data, {e}") from e
    parts = [_with_source(existing_rejected, existing_label), _with_source(new_rejected, new_label)]
    if dups.height:
        parts.append(_clean_as_rejected(dups, "already_loaded").with_columns(pl.lit(new_label).alias("source_file")))
    rejected = pl.concat([p.select(parts[0].columns) for p in parts], how="vertical")
    return MergeResult(clean=clean, rejected=rejected, added=fresh.height, already_loaded=dups.height,
                       rejected_in_file=new_rejected.height)
