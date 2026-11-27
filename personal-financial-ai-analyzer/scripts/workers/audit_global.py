"""Worker: full-scan global audit tables (streaming, column-projected). Run by scripts/run_audit.py.

usage: audit_global.py <out_dir> <missing|distributions|calendar|amounts>
Every statistic is computed over ALL rows (no sampling).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.utils.peak_memory import peak_rss_gb  # noqa: E402
RAW = ROOT / "data/raw/transactions_50M.parquet"


def dist(lf: pl.LazyFrame, col: str, total: int) -> pl.DataFrame:
    return (lf.group_by(col).agg(pl.len().alias("rows")).collect(engine="streaming")
              .with_columns((pl.col("rows") / total).round(6).alias("share")).sort(col))


def main() -> None:
    out, step = Path(sys.argv[1]), sys.argv[2]
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    lf = pl.scan_parquet(RAW)
    cols = lf.collect_schema().names()
    total = lf.select(pl.len()).collect().item()

    if step == "missing":
        _missing(lf, cols, total, out)
    elif step == "distributions":
        _distributions(lf, total, out)
    elif step == "calendar":
        _calendar(lf, out)
    elif step == "amounts":
        _amounts(lf, total, out)
    (out / f"_step_{step}.json").write_text(json.dumps({"step": step, "seconds": round(time.time() - t0, 1),
        "worker_ru_maxrss_gb": peak_rss_gb()}), encoding="utf-8")


def _missing(lf, cols, total, out):
    miss = lf.select(
        *[pl.col(c).is_null().sum().alias(f"{c}__null") for c in cols],
        *[(pl.col(c).cast(pl.String).str.strip_chars() == "").sum().alias(f"{c}__empty") for c in cols],
    ).collect(engine="streaming").row(0, named=True)
    pl.DataFrame([{"column": c, "null": miss[f"{c}__null"], "empty_string": miss[f"{c}__empty"],
                   "rows": total} for c in cols]).write_csv(out / "missing_values.csv")



def _distributions(lf, total, out):
    for col, name in [("currency", "currency_distribution"), ("merchant_category", "category_distribution"),
                      ("transaction_type", "transaction_type_distribution"), ("status", "status_distribution")]:
        dist(lf, col, total).write_csv(out / f"{name}.csv")
    (lf.group_by("transaction_type", "status").agg(pl.len().alias("rows")).collect(engine="streaming")
       .sort("transaction_type", "status").write_csv(out / "type_by_status.csv"))



def _calendar(lf, out):
    ts = pl.col("transaction_timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
    l2 = lf.with_columns(ts.alias("ts"), (pl.col("amount") * 100).round(0).cast(pl.Int64).alias("cents"))
    (l2.group_by(pl.col("ts").dt.strftime("%Y-%m").alias("month"))
       # distinct active accounts per month are counted in audit_partition.py (exact, low memory)
       .agg(pl.len().alias("rows"), (pl.col("status") == "completed").sum().alias("completed_rows"))
       .collect(engine="streaming").sort("month").write_csv(out / "monthly_coverage_base.csv"))
    (l2.group_by(pl.col("ts").dt.hour().alias("hour")).agg(pl.len().alias("rows"))
       .collect(engine="streaming").sort("hour").write_csv(out / "hour_distribution.csv"))
    (l2.group_by(pl.col("ts").dt.weekday().alias("iso_weekday")).agg(pl.len().alias("rows"))
       .collect(engine="streaming").sort("iso_weekday").write_csv(out / "weekday_distribution.csv"))
    days = l2.select(pl.col("ts").dt.date().n_unique().alias("distinct_days"),
                     pl.col("ts").dt.date().min().alias("d0"), pl.col("ts").dt.date().max().alias("d1")
                     ).collect(engine="streaming").row(0, named=True)

    json.dump({k: str(v) for k, v in days.items()}, open(out / "_calendar.json", "w", encoding="utf-8"))


def _amounts(lf, total, out):
    amt = pl.col("amount")
    q = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999, 1.0]
    # Exact quantiles, one currency at a time (a single multi-currency group_by peaked at 3.6 GB RSS)
    currencies = lf.select(pl.col("currency").unique()).collect(engine="streaming")["currency"].sort()
    rows = []
    for cur in currencies:
        a = lf.filter(pl.col("currency") == cur).select("amount").collect(engine="streaming")["amount"]
        rows.append({"currency": cur, "rows": a.len(), **{f"q{x}": a.quantile(x) for x in q}, "mean": a.mean()})
        del a
    pl.DataFrame(rows).write_csv(out / "amount_by_currency.csv")
    la = pl.col("amount").log()
    stats = lf.select(
        (~amt.is_finite()).sum().alias("non_finite_amount"),
        (amt < 0).sum().alias("negative_amount"), (amt == 0).sum().alias("zero_amount"),
        (((amt * 100) - (amt * 100).round(0)).abs() > 1e-6).sum().alias("more_than_2_decimals"),
        (~pl.col("balance_after").is_finite()).sum().alias("non_finite_balance"),
        (pl.col("balance_after") < 0).sum().alias("negative_balance_rows"),
        (((pl.col("balance_after") * 100) - (pl.col("balance_after") * 100).round(0)).abs() > 1e-6).sum()
          .alias("balance_more_than_2_decimals"),
    ).collect(engine="streaming").row(0, named=True)
    logs = lf.select(la.alias("la")).collect(engine="streaming")["la"]
    stats.update(log_q1=logs.quantile(0.25), log_q3=logs.quantile(0.75))
    del logs
    iqr = stats["log_q3"] - stats["log_q1"]
    hi, lo = stats["log_q3"] + 3 * iqr, stats["log_q1"] - 3 * iqr
    outl = lf.select((la > hi).sum().alias("hi"), (la < lo).sum().alias("lo")).collect(engine="streaming").row(0)
    stats.update(outlier_rule="log(amount) outside [Q1-3*IQR, Q3+3*IQR] (investigated, not removed)",
                 outlier_high=int(outl[0]), outlier_low=int(outl[1]),
                 outlier_high_threshold_amount=float(pl.Series([hi]).exp()[0]),
                 outlier_low_threshold_amount=float(pl.Series([lo]).exp()[0]))
    json.dump({"rows": total, "columns": lf.collect_schema().names(), "amount_checks": stats,
               "calendar": json.load(open(out / "_calendar.json", encoding="utf-8"))},
              open(out / "global_stats.json", "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
