"""Build data/samples/demo_personaledger.csv: two users (13 and 16) from Dataset B (PersonaLedger, Capital One
Research, CC BY 4.0, revision c90078ae) in the app's CSV schema, so the E2-B model can be demonstrated.

Mapping (documented, D-24): amount > 0 -> debit (card purchase); merchant_type 'payment' -> transfer (card
payment; neutral); other negative amounts -> refund. Category = merchant_type (lower case). The source states no
currency; the demo labels amounts 'USD' for display only. Status 'completed' (the source has posted card
transactions only). Attribution: data/samples/ATTRIBUTION.md.
"""
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/supplementary/personaledger/raw_generation/normal/transactions.parquet"
OUT = ROOT / "data/samples/demo_personaledger.csv"

d = (pl.scan_parquet(SRC).filter(pl.col("user_id").is_in([13, 16])).collect()
       .sort("user_id", "timestamp")
       .with_columns(pl.when(pl.col("amount") > 0).then(pl.lit("debit"))
                       .when(pl.col("merchant_type") == "payment").then(pl.lit("transfer"))
                       .otherwise(pl.lit("refund")).alias("transaction_type"))
       .filter(pl.col("amount") != 0))
out = d.select(
    pl.format("PL-{}-{}", pl.col("user_id"), pl.int_range(pl.len()).over("user_id")).alias("transaction_id"),
    pl.format("PL-USER-{}", pl.col("user_id")).alias("account_id"),
    "transaction_type", pl.col("amount").abs().round(2).alias("amount"), pl.lit("USD").alias("currency"),
    pl.col("merchant_type").str.to_lowercase().alias("merchant_category"),
    pl.col("timestamp").alias("transaction_timestamp"), pl.lit("completed").alias("status"))
out.write_csv(OUT)
print(OUT, out.height, out.group_by("account_id").len().to_dicts())
