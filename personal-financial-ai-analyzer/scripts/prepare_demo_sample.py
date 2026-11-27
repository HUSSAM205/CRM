"""Create the app's demo files from the PUBLIC dataset (no fabricated records).

data/samples/demo_transactions.csv : full histories of 3 forecast-eligible accounts (dataset schema,
                                     balance_after dropped per D-03), chosen deterministically.
data/samples/sample_bank_export.csv: one of those accounts' completed USD records re-expressed as a
                                     typical bank export (Date, Amount signed, Currency, Category) to
                                     exercise column mapping and the signed-amount rule.
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rules.transaction_mapping import BALANCE_DIRECTION  # noqa: E402
from src.utils.resource_monitor import run_guarded  # noqa: E402

CHILD = r"""
import sys, polars as pl
keys = pl.read_parquet('data/processed/splits/keys_primary.parquet')
pick = keys.sort(['train_active_months', 'account_id'], descending=[True, False]).head(3).select('account_id')
raw = (pl.scan_parquet('data/raw/transactions_50M.parquet').join(pick.lazy(), on='account_id', how='semi')
         .drop('balance_after').collect(engine='streaming').sort('account_id', 'transaction_timestamp'))
raw.write_csv('data/samples/demo_transactions.csv')
print(raw.height)
"""


def main() -> None:
    (ROOT / "data/samples").mkdir(parents=True, exist_ok=True)
    g = run_guarded([sys.executable, "-c", CHILD], cwd=ROOT)
    if not g.ok:
        raise SystemExit(g.killed_reason or g.stderr_tail)
    demo = pl.read_csv(ROOT / "data/samples/demo_transactions.csv", infer_schema=False)
    acc = demo["account_id"].min()
    one = demo.filter((pl.col("account_id") == acc) & (pl.col("currency") == "USD") & (pl.col("status") == "completed"))
    sign = pl.col("transaction_type").replace_strict(BALANCE_DIRECTION, return_dtype=pl.Int64)
    bank = one.select(pl.col("transaction_timestamp").str.slice(0, 10).alias("Date"),
                      (pl.col("amount").cast(pl.Float64) * sign).round(2).alias("Amount"),
                      pl.col("currency").alias("Currency"), pl.col("merchant_category").alias("Category"))
    bank.write_csv(ROOT / "data/samples/sample_bank_export.csv")
    print(f"demo rows={demo.height} accounts={demo['account_id'].n_unique()}; bank export rows={bank.height} ({acc})")


if __name__ == "__main__":
    main()
