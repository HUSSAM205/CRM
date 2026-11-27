"""Analyzer insights (master audit 6.2-6.7): period spending, statistics, income, cash flow, recurring
payment candidates, behaviour changes and transparent indicators.

Every function is deterministic and works on validated, completed records of ONE account and ONE currency
(amounts in different currencies are never combined). Money is integer cents. Nothing here infers salary,
personality or lifestyle: incoming money is reported as "recorded inflows"; repeated payments are
"recurring payment candidates" with their supporting transactions and a stated confidence.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from src.analytics.aggregation import Summaries
from src.rules.transaction_mapping import FEE, INFLOW, OUTFLOW, REFUND
from src.rules.transaction_status import is_counted

# signed contribution to "spending": outflow and fee add, refund subtracts (same definition as expenses_cents)
_SPEND = (pl.when(pl.col("meaning").is_in([OUTFLOW, FEE])).then(pl.col("amount_cents"))
            .when(pl.col("meaning") == REFUND).then(-pl.col("amount_cents")).otherwise(0))


def scope(clean: pl.DataFrame, account: str, currency: str) -> pl.DataFrame:
    """Completed, counted records of one account and one currency."""
    return clean.filter((pl.col("account_id") == account) & (pl.col("currency") == currency) & is_counted())


def period_spending(clean: pl.DataFrame, account: str, currency: str, freq: str = "month") -> pl.DataFrame:
    """Spending (outflow + fee - refund) per day, ISO week or month; periods without spending are absent."""
    every = {"day": "1d", "week": "1w", "month": "1mo"}[freq]
    d = scope(clean, account, currency).with_columns(_SPEND.alias("spend_cents"))
    return (d.sort("transaction_timestamp")
              .group_by_dynamic("transaction_timestamp", every=every, label="left")
              .agg(pl.col("spend_cents").sum(), pl.len().alias("records"))
              .rename({"transaction_timestamp": "period_start"}))


def monthly_series(s: Summaries, account: str, currency: str, field: str = "expenses_cents") -> pl.DataFrame:
    """Monthly values over the full observed range; months without records are filled with 0."""
    m = s.monthly.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    if m.is_empty():
        return pl.DataFrame({"month": [], field: []}, schema={"month": pl.String, field: pl.Int64})
    from src.experiments.data_splitting import month_range
    months = month_range(m["month"].min(), m["month"].max())
    return (pl.DataFrame({"month": months}).join(m.select("month", field), on="month", how="left")
              .with_columns(pl.col(field).fill_null(0)))


def spending_statistics(s: Summaries, account: str, currency: str) -> dict:
    """Average, median, highest and lowest month and recent change of monthly expenses."""
    ser = monthly_series(s, account, currency)
    if ser.is_empty():
        return {"months": 0}
    v = ser["expenses_cents"].to_numpy()
    hi, lo = int(v.argmax()), int(v.argmin())
    out = {"months": len(v), "mean_cents": int(round(v.mean())), "median_cents": int(round(float(np.median(v)))),
           "highest_month": ser["month"][hi], "highest_cents": int(v[hi]),
           "lowest_month": ser["month"][lo], "lowest_cents": int(v[lo]), "recent_change_pct": None}
    if len(v) >= 6 and v[-6:-3].sum() > 0:
        out["recent_change_pct"] = float((v[-3:].sum() - v[-6:-3].sum()) / v[-6:-3].sum() * 100)
        out["recent_change_basis"] = f"last 3 months ({ser['month'][-3]}..{ser['month'][-1]}) vs the 3 before"
    return out


def income_analysis(clean: pl.DataFrame, s: Summaries, account: str, currency: str) -> dict:
    """Recorded inflows (credit, deposit, interest): monthly totals, frequency, variability, repeats.
    These are NOT labelled as salary: the data cannot show what an inflow is."""
    ser = monthly_series(s, account, currency, "income_cents")
    d = scope(clean, account, currency).filter(pl.col("meaning") == INFLOW)
    v = ser["income_cents"].to_numpy() if not ser.is_empty() else np.array([])
    mean = float(v.mean()) if len(v) else 0.0
    by_type = d.group_by("transaction_type").agg(pl.col("amount_cents").sum(), pl.len().alias("records")) \
               .sort("amount_cents", descending=True)
    return {"months": len(v), "months_with_inflows": int((v > 0).sum()), "records": d.height,
            "mean_monthly_cents": int(round(mean)),
            "coefficient_of_variation": float(v.std() / mean) if mean > 0 else None,
            "by_type": by_type, "monthly": ser,
            "recurring_candidates": recurring_candidates(d.with_columns(pl.lit(OUTFLOW).alias("meaning")),
                                                         account, currency, include_meanings=(OUTFLOW,)),
            "note": "Recorded inflows only. Whether any of them is salary cannot be determined from the data."}


def cash_flow(s: Summaries, account: str, currency: str) -> pl.DataFrame:
    """Monthly inflows, outflows (expenses), net and expense-to-income ratio (only where income > 0)."""
    inc = monthly_series(s, account, currency, "income_cents")
    exp = monthly_series(s, account, currency, "expenses_cents")
    if inc.is_empty():
        return inc
    return (inc.join(exp, on="month")
               .with_columns((pl.col("income_cents") - pl.col("expenses_cents")).alias("net_cents"),
                             pl.when(pl.col("income_cents") > 0)
                               .then(pl.col("expenses_cents") / pl.col("income_cents")).otherwise(None)
                               .alias("expense_to_income")))


def recurring_candidates(d: pl.DataFrame, account: str | None = None, currency: str | None = None,
                         include_meanings: tuple[str, ...] = (OUTFLOW,), amount_tol: float = 0.05,
                         min_occurrences: int = 3) -> pl.DataFrame:
    """Recurring payment candidates: same category, amounts within +/-5% of the group's median, at a regular
    weekly (5-9 days) or monthly (25-35 days) median interval with interval variation below 25%.
    Confidence: 'high' with >= 4 occurrences and interval variation < 15%, otherwise 'medium'.
    A candidate is not a confirmed subscription; its supporting transactions are listed."""
    if account is not None:
        d = d.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
    d = d.filter(pl.col("meaning").is_in(list(include_meanings))).sort("transaction_timestamp")
    out = []
    for (cat,), g in d.group_by(["merchant_category"]):
        amts = g["amount_cents"].to_numpy().astype(float)
        ts = g["transaction_timestamp"].to_list()
        ids = g["transaction_id"].to_list()
        used = np.zeros(len(amts), bool)
        for i in np.argsort(amts):
            if used[i] or amts[i] <= 0:
                continue
            members = np.where(~used & (np.abs(amts - amts[i]) <= amount_tol * amts[i]))[0]
            if len(members) < min_occurrences:
                continue
            members = sorted(members, key=lambda k: ts[k])
            gaps = np.diff([ts[k].timestamp() for k in members]) / 86400
            med = float(np.median(gaps))
            cv = float(gaps.std() / med) if med > 0 else np.inf
            period = "weekly" if 5 <= med <= 9 else "monthly" if 25 <= med <= 35 else None
            if period and cv < 0.25:
                used[members] = True
                out.append({"merchant_category": cat, "period": period, "occurrences": len(members),
                            "typical_amount_cents": int(np.median(amts[members])),
                            "median_interval_days": round(med, 1), "interval_variation": round(cv, 3),
                            "first": ts[members[0]].date().isoformat(), "last": ts[members[-1]].date().isoformat(),
                            "confidence": "high" if len(members) >= 4 and cv < 0.15 else "medium",
                            "supporting_transactions": ", ".join(ids[k] for k in members[:12])})
    schema = {"merchant_category": pl.String, "period": pl.String, "occurrences": pl.Int64,
              "typical_amount_cents": pl.Int64, "median_interval_days": pl.Float64, "interval_variation": pl.Float64,
              "first": pl.String, "last": pl.String, "confidence": pl.String, "supporting_transactions": pl.String}
    return pl.DataFrame(out, schema=schema).sort("typical_amount_cents", descending=True)


def behaviour_changes(clean: pl.DataFrame, s: Summaries, account: str, currency: str,
                      min_change_pct: float = 25.0, min_abs_cents: int = 1000) -> dict:
    """Category spending last 3 months vs the 3 before (both totals over the same number of months);
    concentration; repeated small expenses; large isolated expenses. Factual comparisons only."""
    months = monthly_series(s, account, currency)["month"].to_list()      # contiguous calendar months
    res = {"increasing": [], "declining": [], "basis": None, "top_category_share": None,
           "repeated_small": [], "large_isolated": []}
    if len(months) >= 6:
        recent, prior = months[-3:], months[-6:-3]
        c = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency))
        r = c.filter(pl.col("month").is_in(recent)).group_by("merchant_category").agg(pl.col("net_spending_cents").sum().alias("recent"))
        p = c.filter(pl.col("month").is_in(prior)).group_by("merchant_category").agg(pl.col("net_spending_cents").sum().alias("prior"))
        j = r.join(p, on="merchant_category", how="full", coalesce=True).fill_null(0)
        for row in j.iter_rows(named=True):
            diff = row["recent"] - row["prior"]
            if abs(diff) >= min_abs_cents and row["prior"] > 0 and abs(diff) / row["prior"] * 100 >= min_change_pct:
                item = {"category": row["merchant_category"], "prior_cents": row["prior"], "recent_cents": row["recent"],
                        "change_pct": round(diff / row["prior"] * 100, 1)}
                res["increasing" if diff > 0 else "declining"].append(item)
        res["basis"] = f"{recent[0]}..{recent[-1]} vs {prior[0]}..{prior[-1]}"
        tot = j.filter(pl.col("recent") > 0)
        if tot.height and tot["recent"].sum() > 0:
            top = tot.sort("recent", descending=True).row(0, named=True)
            res["top_category_share"] = {"category": top["merchant_category"],
                                         "share": round(top["recent"] / tot["recent"].sum(), 3)}
    d = scope(clean, account, currency).filter(pl.col("meaning") == OUTFLOW)
    if d.height >= 10:
        med = float(d["amount_cents"].median())
        last = d.filter(pl.col("month").is_in(months[-3:])) if months else d
        small = last.filter(pl.col("amount_cents") <= 0.2 * med).group_by("merchant_category").agg(
            pl.len().alias("count"), pl.col("amount_cents").sum().alias("total_cents")).filter(pl.col("count") >= 5)
        res["repeated_small"] = small.sort("count", descending=True).to_dicts()
        res["large_isolated"] = (d.filter(pl.col("amount_cents") >= 5 * med)
                                   .select("transaction_id", pl.col("transaction_timestamp").dt.date().cast(pl.String)
                                           .alias("date"), "merchant_category", "amount_cents")
                                   .sort("amount_cents", descending=True).head(10).to_dicts())
        res["median_outflow_cents"] = int(med)
    return res


def indicators(clean: pl.DataFrame, s: Summaries, account: str, currency: str,
               budgets: dict[str, int] | None = None) -> list[dict]:
    """Transparent descriptive indicators. No aggregate 'health score' is produced (master audit 6.7):
    each indicator states its formula, value and how to read it; missing inputs give None with a reason."""
    exp = monthly_series(s, account, currency)["expenses_cents"].to_numpy()
    cf = cash_flow(s, account, currency)
    out = []
    if len(exp) >= 3 and exp.mean() > 0:
        out.append({"indicator": "Spending stability", "value": round(float(exp.std() / exp.mean()), 3),
                    "formula": "standard deviation / mean of monthly expenses (coefficient of variation)",
                    "reading": "lower = steadier spending; above 1 means very irregular months"})
    else:
        out.append({"indicator": "Spending stability", "value": None, "formula": "CV of monthly expenses",
                    "reading": "needs at least 3 months with spending"})
    if not cf.is_empty():
        out.append({"indicator": "Cash-flow consistency",
                    "value": round(float((cf["net_cents"] >= 0).mean()), 3),
                    "formula": "share of months where recorded inflows >= expenses",
                    "reading": "transaction-derived only; other accounts and opening balances are unknown"})
        inc, ex = int(cf["income_cents"].sum()), int(cf["expenses_cents"].sum())
        out.append({"indicator": "Net inflow ratio (savings-rate proxy)",
                    "value": round((inc - ex) / inc, 3) if inc > 0 else None,
                    "formula": "(recorded inflows - expenses) / recorded inflows over the whole period",
                    "reading": "not a verified savings rate: transfers are excluded and inflows are not "
                               "known to be income" if inc > 0 else "no recorded inflows"})
    rec = recurring_candidates(scope(clean, account, currency))
    if len(exp) and exp.mean() > 0:
        monthly_rec = sum(r["typical_amount_cents"] * (52 / 12 if r["period"] == "weekly" else 1)
                          for r in rec.iter_rows(named=True))
        out.append({"indicator": "Recurring payment burden", "value": round(float(monthly_rec / exp.mean()), 3),
                    "formula": "monthly equivalent of recurring payment candidates / mean monthly expenses",
                    "reading": f"{rec.height} candidate(s); candidates are not confirmed subscriptions"})
    if budgets:
        last = s.months(account, currency)[-1]
        c = s.category.filter((pl.col("account_id") == account) & (pl.col("currency") == currency)
                              & (pl.col("month") == last))
        spent = dict(zip(c["merchant_category"], c["net_spending_cents"]))
        active = {k: v for k, v in budgets.items() if v > 0}
        ok = sum(1 for k, v in active.items() if spent.get(k, 0) <= v)
        out.append({"indicator": f"Budget adherence ({last})", "value": round(ok / len(active), 3) if active else None,
                    "formula": "share of categories with a budget whose spending is within it",
                    "reading": "1.0 = every budgeted category within its limit"})
    return out
