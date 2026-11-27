"""Dataset B (PersonaLedger, CC BY 4.0, revision c90078ae) quality and forecasting-suitability audit.

Read-only on data/supplementary/; lazy Polars scans, run under the memory guard. Writes
reports/experiments/dataset_b/quality.json and the monthly panel data/supplementary/derived/monthly_spend.parquet
(user x month spending = sum of positive amounts; negative amounts are reported separately, never mixed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/supplementary/personaledger/raw_generation/normal/transactions.parquet"
FRAUD = ROOT / "data/supplementary/personaledger/identity_theft_1months/test.parquet"
OUT = ROOT / "reports/experiments/dataset_b"
DER = ROOT / "data/supplementary/derived"


def main() -> None:
    lf = pl.scan_parquet(SRC)
    base = lf.select(
        pl.len().alias("rows"), pl.col("user_id").n_unique().alias("users"),
        pl.col("timestamp").min().alias("t_min"), pl.col("timestamp").max().alias("t_max"),
        *[pl.col(c).null_count().alias(f"null_{c}") for c in ("user_id", "timestamp", "merchant_name", "merchant_type",
                                                              "card_present_or_not", "amount")],
        (pl.col("amount") < 0).sum().alias("negative_amounts"), (pl.col("amount") == 0).sum().alias("zero_amounts"),
        (~pl.col("amount").is_finite()).sum().alias("non_finite_amounts"),
        pl.col("merchant_type").n_unique().alias("merchant_types"),
        pl.col("merchant_name").n_unique().alias("merchant_names"),
    ).collect(engine="streaming").to_dicts()[0]
    q = lf.filter(pl.col("amount") > 0).select([pl.col("amount").quantile(x).alias(f"q{x}") for x in
                                                (0.01, 0.25, 0.5, 0.75, 0.99, 1.0)]).collect(engine="streaming").to_dicts()[0]
    bad_ts = lf.select(pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
                       .is_null().sum()).collect(engine="streaming").item()
    top_types = (lf.group_by("merchant_type").agg(pl.len().alias("n")).sort("n", descending=True).head(15)
                   .collect(engine="streaming").to_dicts())
    monthly = (lf.filter(pl.col("amount") > 0)
                 .group_by("user_id", pl.col("timestamp").str.slice(0, 7).alias("month"))
                 .agg((pl.col("amount") * 100).round(0).cast(pl.Int64).sum().alias("spend_cents"), pl.len().alias("n"))
                 .collect(engine="streaming"))
    DER.mkdir(parents=True, exist_ok=True)
    monthly.write_parquet(DER / "monthly_spend.parquet")
    months = sorted(monthly["month"].unique().to_list())
    per_user = monthly.group_by("user_id").agg(pl.len().alias("active_months"), pl.col("month").min().alias("first"),
                                               pl.col("month").max().alias("last"))
    # within-user lag-1 autocorrelation of monthly spending (zero-filled within each user's own span)
    piv = monthly.pivot(on="month", index="user_id", values="spend_cents").fill_null(0)
    Y = piv.select([m for m in months]).to_numpy().astype(float)
    ac, zeros, cells = [], 0, 0
    for row in Y:
        nzr = np.nonzero(row)[0]
        if len(nzr):
            span = row[nzr[0]:nzr[-1] + 1]
            zeros, cells = zeros + int((span == 0).sum()), cells + len(span)
    for row in Y:
        nz = np.nonzero(row)[0]
        if len(nz) >= 13:
            s = row[nz[0]:nz[-1] + 1]
            if s[1:].std() > 0 and s[:-1].std() > 0:
                ac.append(np.corrcoef(s[1:], s[:-1])[0, 1])
    fr = pl.scan_parquet(FRAUD).select(pl.len().alias("rows"), pl.col("seq_id").n_unique().alias("sequences"),
                                       pl.col("is_fraud").sum().alias("fraud_rows"),
                                       pl.col("timestamp").min().cast(pl.String).alias("t_min"),
                                       pl.col("timestamp").max().cast(pl.String).alias("t_max")).collect().to_dicts()[0]
    res = {"dataset_id": "B-PERSONALEDGER-NORMAL", **base, "unparseable_timestamps": bad_ts, "amount_quantiles_positive": q,
           "top_merchant_types": top_types, "months": months, "n_months": len(months),
           "users_by_active_months": per_user.group_by("active_months").len().sort("active_months").to_dicts(),
           "users_with_ge_12_active_months": int((per_user["active_months"] >= 12).sum()),
           "share_zero_user_months_within_span": zeros / cells,
           "note_partial_months": "each user's first and last month are partial (users start and stop mid-month); "
                                  "experiments exclude them as targets",
           "mean_within_user_lag1_autocorrelation": float(np.mean(ac)) if ac else None,
           "autocorrelation_users": len(ac),
           "identity_theft_1m_test": fr}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "quality.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k not in ("top_merchant_types", "months", "users_by_active_months")}, indent=1, default=str))
    print("months", months[0], "..", months[-1])


if __name__ == "__main__":
    sys.exit(main())
