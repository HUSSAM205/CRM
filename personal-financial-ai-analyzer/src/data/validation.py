"""Row-level validation shared by the dataset pipeline and user CSV uploads.

Every record ends up in exactly one of two frames:
  * clean    - typed, normalized, with `amount_cents` (exact integer money) and `month`
  * rejected - original values kept as strings plus a `reject_reason`
No record is dropped silently (HW1 4.5(2), HW2 Table 10.1).

Rejection reasons (checked in this order; first failing rule wins):
  missing_<column>          required value is null/empty
  invalid_timestamp         not parseable as YYYY-MM-DD HH:MM:SS
  invalid_amount            not a finite number
  amount_out_of_range       |amount| > 1e12 (cents would overflow / lose exactness; P0/P1 audit fix)
  negative_amount           dataset convention is non-negative magnitudes (HW1 Table 4.2)
  amount_precision          more than 2 decimal places (cannot be represented in cents)
  unknown_currency          not one of the six supported ISO codes
  unknown_status            not completed/pending/failed/reversed
  duplicate_transaction_id  a previous record already used this id (first one kept)
Unknown transaction types are NOT rejected: they are kept with meaning 'unresolved' and
excluded from totals (never guessed).
"""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from src.data.schema import (ALLOWED_CURRENCIES, ALLOWED_STATUSES, TIMESTAMP_FORMAT,
                             UNCATEGORIZED)
from src.rules.transaction_mapping import meaning_expr

CORE_REQUIRED = ["transaction_id", "account_id", "transaction_type", "amount", "currency",
                 "transaction_timestamp", "status"]
_PRECISION_TOL = 1e-6
# Exact cents are verified up to 1e13 (reports/audit/financial_calculation_audit.md); int64 cents overflow
# near 9.2e16. 1e12 currency units is far above any personal-finance amount and keeps a wide margin.
MAX_ABS_AMOUNT = 1e12
# Polars int64 sums wrap around silently on overflow (measured: 100,000 x 999,999,999,999.99 summed to a
# negative total). Every total over a file is bounded by the sum of absolute amounts, so a file whose
# absolute total reaches 2**62 cents (half the int64 range, margin for intermediate sums) is refused as a whole.
SAFE_TOTAL_CENTS = 2 ** 62


class TotalOutOfRangeError(ValueError):
    """The amounts of one file add up beyond the range in which integer-cent totals are exact."""


def check_total_range(clean: pl.DataFrame) -> None:
    """Raise TotalOutOfRangeError if any aggregate of `clean` could overflow int64 cents (audit M-02)."""
    if clean.height and float(clean["amount_cents"].cast(pl.Float64).abs().sum()) >= SAFE_TOTAL_CENTS:
        raise TotalOutOfRangeError("the amounts in this file add up to more than the supported range "
                                   f"({SAFE_TOTAL_CENTS / 100:,.0f} per file); totals would not be exact")


@dataclass
class ValidationResult:
    clean: pl.DataFrame
    rejected: pl.DataFrame

    @property
    def reason_counts(self) -> dict[str, int]:
        if self.rejected.is_empty():
            return {}
        vc = self.rejected.group_by("reject_reason").len().sort("reject_reason")
        return dict(zip(vc["reject_reason"].to_list(), vc["len"].to_list()))


def _as_str(col: str) -> pl.Expr:
    return pl.col(col).cast(pl.String).str.strip_chars()


def validate_transactions(df: pl.DataFrame) -> ValidationResult:
    """Validate a frame that already uses the canonical column names."""
    missing_cols = [c for c in CORE_REQUIRED if c not in df.columns]
    if missing_cols:
        raise ValueError(f"missing required columns: {missing_cols}")
    if "merchant_category" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.String).alias("merchant_category"))
    if "balance_after" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.Float64).alias("balance_after"))

    work = df.with_row_index("_row").with_columns(
        *[_as_str(c).alias(f"_s_{c}") for c in CORE_REQUIRED + ["merchant_category"]],
    ).with_columns(
        pl.col("_s_transaction_timestamp").str.strptime(pl.Datetime("us"), TIMESTAMP_FORMAT,
                                                       strict=False).alias("_ts"),
        pl.col("_s_amount").cast(pl.Float64, strict=False).alias("_amt"),
        pl.col("_s_currency").str.to_uppercase().alias("_cur"),
        pl.col("_s_status").str.to_lowercase().alias("_st"),
    )

    reason = pl.lit(None, dtype=pl.String)
    checks: list[tuple[pl.Expr, str]] = []
    for c in CORE_REQUIRED:
        checks.append(((pl.col(f"_s_{c}").is_null()) | (pl.col(f"_s_{c}") == ""), f"missing_{c}"))
    checks += [
        (pl.col("_ts").is_null(), "invalid_timestamp"),
        (pl.col("_amt").is_null() | ~pl.col("_amt").is_finite(), "invalid_amount"),
        (pl.col("_amt").abs() > MAX_ABS_AMOUNT, "amount_out_of_range"),
        (pl.col("_amt") < 0, "negative_amount"),
        (((pl.col("_amt") * 100) - (pl.col("_amt") * 100).round(0)).abs() > _PRECISION_TOL,
         "amount_precision"),
        (~pl.col("_cur").is_in(sorted(ALLOWED_CURRENCIES)), "unknown_currency"),
        (~pl.col("_st").is_in(sorted(ALLOWED_STATUSES)), "unknown_status"),
    ]
    # Build "first failing rule wins" from the last rule backwards.
    for cond, name in reversed(checks):
        reason = pl.when(cond).then(pl.lit(name)).otherwise(reason)
    work = work.with_columns(reason.alias("reject_reason"))

    # Duplicates: among otherwise-valid rows, keep the first occurrence of each id.
    dup = (pl.col("reject_reason").is_null()
           & pl.col("_s_transaction_id").is_duplicated()
           & ~pl.col("_row").is_in(
               work.filter(pl.col("reject_reason").is_null())
                   .group_by("_s_transaction_id").agg(pl.col("_row").min())["_row"].implode()))
    work = work.with_columns(
        pl.when(dup).then(pl.lit("duplicate_transaction_id"))
          .otherwise(pl.col("reject_reason")).alias("reject_reason"))

    rejected = (work.filter(pl.col("reject_reason").is_not_null())
                    .select(pl.col("_row").alias("source_row"),
                            *[pl.col(f"_s_{c}").alias(c) for c in CORE_REQUIRED],
                            pl.col("reject_reason")))

    clean = (work.filter(pl.col("reject_reason").is_null())
                 .select(
                     pl.col("_row").alias("source_row"),
                     pl.col("_s_transaction_id").alias("transaction_id"),
                     pl.col("_s_account_id").alias("account_id"),
                     pl.col("_s_transaction_type").str.to_lowercase().alias("transaction_type"),
                     pl.col("_amt").alias("amount"),
                     (pl.col("_amt") * 100).round(0).cast(pl.Int64, strict=True).alias("amount_cents"),
                     pl.col("_cur").alias("currency"),
                     # categories are normalized to lowercase, except the canonical fallback label,
                     # which must be identical whether it came from a blank or from keyword rules
                     pl.when(pl.col("_s_merchant_category").is_null()
                             | (pl.col("_s_merchant_category") == "")
                             | (pl.col("_s_merchant_category").str.to_lowercase() == UNCATEGORIZED.lower()))
                       .then(pl.lit(UNCATEGORIZED))
                       .otherwise(pl.col("_s_merchant_category").str.to_lowercase())
                       .alias("merchant_category"),
                     pl.col("balance_after").cast(pl.Float64, strict=False),
                     pl.col("_ts").alias("transaction_timestamp"),
                     pl.col("_st").alias("status"),
                 )
                 .with_columns(pl.col("transaction_timestamp").dt.strftime("%Y-%m").alias("month"),
                               meaning_expr()))
    return ValidationResult(clean=clean, rejected=rejected)
