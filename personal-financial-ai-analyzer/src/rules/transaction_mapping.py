"""Fixed mapping from transaction_type to financial meaning (HW2 section 5.2).

Evidence for each direction: reports/verification/ledger_semantics_report.md, which measures,
over every completed record of the dataset, the sign of the change in balance_after when
records of one account are ordered by transaction_id.

Meanings:
  outflow   - spending that leaves the account (counts as expense, has a category)
  fee       - bank charge (counts as expense, reported on its own line, not in category spend)
  inflow    - money received (reported as income/inflow; NEVER assumed to be salary)
  refund    - money returned; reduces spending of its own category/month/currency
  transfer  - movement between the user's accounts; excluded from income and expenses
              (dataset has no counterparty field, see docs/requirements_conflicts.md CF-08)
  unresolved- unknown type; excluded from all totals and reported, never guessed
"""
from __future__ import annotations

import polars as pl

OUTFLOW, FEE, INFLOW, REFUND, TRANSFER, UNRESOLVED = (
    "outflow", "fee", "inflow", "refund", "transfer", "unresolved")

TYPE_MEANING: dict[str, str] = {
    "debit": OUTFLOW,
    "withdrawal": OUTFLOW,
    "fee": FEE,
    "credit": INFLOW,
    "deposit": INFLOW,
    "interest": INFLOW,
    "refund": REFUND,
    "transfer": TRANSFER,
}

# Direction of the balance change for a completed record (+1 increases balance).
BALANCE_DIRECTION: dict[str, int] = {
    "debit": -1, "withdrawal": -1, "fee": -1, "transfer": -1,
    "credit": +1, "deposit": +1, "interest": +1, "refund": +1,
}


def meaning_expr(type_col: str = "transaction_type") -> pl.Expr:
    """Polars expression mapping transaction_type to its meaning ('unresolved' if unknown)."""
    return (pl.col(type_col).str.to_lowercase()
            .replace_strict(TYPE_MEANING, default=UNRESOLVED, return_dtype=pl.String)
            .alias("meaning"))


def meaning_of(transaction_type: str | None) -> str:
    if transaction_type is None:
        return UNRESOLVED
    return TYPE_MEANING.get(str(transaction_type).lower(), UNRESOLVED)
