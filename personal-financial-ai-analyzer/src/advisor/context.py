"""Financial context for the Advisor: what is KNOWN (calculated from validated transactions or supplied by
the user) and what is UNKNOWN. Every value carries its source so the UI can label facts, calculations and
assumptions separately (master audit 8.1, 10). Nothing is invented: unknown values stay None."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

from src.analytics import insights as I
from src.analytics.aggregation import Summaries
from src.utils.configuration import load_config

CFG = load_config("advisor")


@dataclass
class UserFacts:
    """Facts only the user can supply. None = not provided (never assumed)."""
    current_savings_cents: int | None = None
    current_balance_cents: int | None = None
    monthly_income_cents: int | None = None
    monthly_obligations_cents: int | None = None


@dataclass
class FinancialContext:
    account: str
    currency: str
    months_observed: int
    window: list[str]                         # months used for averages
    avg_inflow_cents: int                     # recorded inflows (not known to be income)
    avg_expenses_cents: int
    avg_net_cents: int
    category_avg_recent_cents: dict[str, int]  # last 3 calendar months
    category_prior_avg_cents: dict[str, int]   # average of the 9 calendar months before those 3 (0-filled)
    recurring_monthly_cents: int
    user: UserFacts = field(default_factory=UserFacts)

    @property
    def monthly_income_basis(self) -> tuple[int, str]:
        """User-supplied income if given, else recorded inflows (labelled as such)."""
        if self.user.monthly_income_cents is not None:
            return self.user.monthly_income_cents, "user-provided monthly income"
        return self.avg_inflow_cents, f"average recorded inflows ({self.window[0]}..{self.window[-1]})"

    @property
    def monthly_surplus_cents(self) -> tuple[int, str]:
        inc, src = self.monthly_income_basis
        obl = self.user.monthly_obligations_cents or 0
        note = f"{src} − average expenses" + (" − user-provided obligations" if obl else "")
        return inc - self.avg_expenses_cents - obl, note

    def unknowns(self) -> list[str]:
        out = []
        if self.user.current_balance_cents is None:
            out.append("current bank balance")
        if self.user.monthly_income_cents is None:
            out.append("verified income (only recorded inflows are known)")
        if self.user.monthly_obligations_cents is None:
            out.append("upcoming obligations (rent, loans, bills not in this file)")
        out.append("other accounts and assets not in this file")
        return out


def build_context(clean: pl.DataFrame, s: Summaries, account: str, currency: str,
                  user: UserFacts | None = None) -> FinancialContext:
    n = CFG["history_months_for_averages"]
    cf = I.cash_flow(s, account, currency)
    months = cf["month"].to_list() if not cf.is_empty() else []
    win = months[-n:]
    w = cf.filter(pl.col("month").is_in(win)) if win else cf
    avg = (lambda c: int(round(float(w[c].mean())))) if w.height else (lambda c: 0)
    cat = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    recent, prior = months[-3:], months[-CFG["reduction"]["long_run_months"]:-3]
    rec_avg, prior_avg = {}, {}
    for c in sorted(cat["merchant_category"].unique().to_list()):
        cc = cat.filter(pl.col("merchant_category") == c)
        by = dict(zip(cc["month"], cc["net_spending_cents"]))
        rec_avg[c] = int(round(float(np.mean([by.get(m, 0) for m in recent])))) if recent else 0
        prior_avg[c] = int(round(float(np.mean([by.get(m, 0) for m in prior])))) if prior else 0
    rec = I.recurring_candidates(I.scope(clean, account, currency))
    rec_m = int(round(sum(r["typical_amount_cents"] * (52 / 12 if r["period"] == "weekly" else 1)
                          for r in rec.iter_rows(named=True))))
    return FinancialContext(account, currency, len(months), win, avg("income_cents"), avg("expenses_cents"),
                            avg("net_cents"), rec_avg, prior_avg, rec_m, user or UserFacts())
