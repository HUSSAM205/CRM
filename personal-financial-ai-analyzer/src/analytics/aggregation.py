"""Summary objects the dashboard and assistant query (HW1 3.2.4: queries hit summary tables).

A `Summaries` bundle is computed once per validated dataset; every UI number and every assistant
answer reads from it, so the two can never disagree (HW2 10.4).
"""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from src.analytics.financial_metrics import category_spending, monthly_summary
from src.rules.transaction_status import status_report


@dataclass(frozen=True)
class Summaries:
    monthly: pl.DataFrame            # account x currency x month
    category: pl.DataFrame           # account x currency x month x category
    status: pl.DataFrame             # currency x status counts
    accounts: list[str]
    currencies: list[str]

    def months(self, account: str, currency: str) -> list[str]:
        return sorted(self.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
                      ["month"].unique().to_list())


def build_summaries(clean: pl.DataFrame) -> Summaries:
    monthly = monthly_summary(clean)
    return Summaries(monthly=monthly, category=category_spending(clean), status=status_report(clean),
                     accounts=sorted(clean["account_id"].unique().to_list()),
                     currencies=sorted(clean["currency"].unique().to_list()))


def period_totals(s: Summaries, account: str, currency: str, months: list[str] | None = None) -> dict:
    m = s.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    if months is not None:
        m = m.filter(pl.col("month").is_in(months))
    cols = ["income_cents", "expenses_cents", "net_cash_flow_cents", "transfer_cents", "fee_cents",
            "refund_cents", "completed_records", "excluded_status_records"]
    return {c: int(m[c].sum()) for c in cols}
