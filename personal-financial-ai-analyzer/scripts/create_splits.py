"""Gate 6: experimental splits and working subsets (HW2 6.3, 8.2; DECISIONS D-08, D-14).

Outputs (data/processed/splits/):
  eligible_series.parquet          all account-currency series with >= 12 active TRAIN months
  panel_<name>.parquet             monthly expenses panels (31 months, 0 = no expenses) for:
                                   primary (seed 42), seed43, seed44 (robustness resamples),
                                   disjoint (accounts disjoint from primary; CF-05)
  anomaly_accounts.parquet         seeded accounts for the anomaly experiment
  anomaly_transactions.parquet     their validated transactions (all periods)
  split_metadata.json              actual counts per split and subset
Heavy reads run in guarded child processes (configs/resource_limits.yaml).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments.data_splitting import ALL_MONTHS, TEST, TRAIN, VALIDATION  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402
from src.utils.resource_monitor import run_guarded  # noqa: E402

CFG = load_config("experiments")
OUT = ROOT / CFG["outputs"]["splits_dir"]
PANEL_CHILD = r"""
import sys, polars as pl
sys.path.insert(0, '.')
from src.experiments.data_splitting import ALL_MONTHS
keys = pl.read_parquet(sys.argv[1])
panel = (pl.scan_parquet('data/processed/monthly/*.parquet')
           .join(keys.lazy(), on=['account_id', 'currency'], how='semi')
           .select('account_id', 'currency', 'month', 'expenses_cents')
           .collect(engine='streaming'))
wide = (keys.join(panel.pivot(on='month', index=['account_id', 'currency'], values='expenses_cents'),
                  on=['account_id', 'currency'], how='left')
            .with_columns([pl.col(m).fill_null(0).cast(pl.Int64) if m in panel['month'].unique().to_list()
                           else pl.lit(0, dtype=pl.Int64).alias(m) for m in ALL_MONTHS])
            .select('account_id', 'currency', 'train_active_months', *ALL_MONTHS))
wide.write_parquet(sys.argv[2])
print(wide.height)
"""
ANOMALY_CHILD = r"""
import sys, polars as pl
sys.path.insert(0, '.')
from src.data.validation import validate_transactions
acc = pl.read_parquet(sys.argv[1])
raw = (pl.scan_parquet('data/raw/transactions_50M.parquet')
         .join(acc.lazy(), on='account_id', how='semi').collect(engine='streaming'))
res = validate_transactions(raw)
assert res.rejected.is_empty(), res.reason_counts
res.clean.drop('balance_after').write_parquet(sys.argv[2])   # D-03: balance never carried forward
print(res.clean.height)
"""


def guarded_child(code: str, *args: str) -> str:
    g = run_guarded([sys.executable, "-c", code, *args], cwd=ROOT)
    if not g.ok:
        raise SystemExit(f"child failed: {g.killed_reason or g.stderr_tail}")
    print(f"  child ok {g.seconds}s peak_rss={g.peak_rss_gb}GB", flush=True)
    return g.stdout_tail.strip().splitlines()[-1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fc = CFG["forecasting"]
    stats = pl.read_parquet(ROOT / "data/processed/series_stats/*.parquet")
    elig = (stats.filter(pl.col("train_active_months") >= fc["min_active_train_months"])
                 .sort("account_id", "currency"))          # deterministic order before seeded sampling
    elig.write_parquet(OUT / "eligible_series.parquet")
    meta: dict = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                  "split": {"train": TRAIN, "validation": VALIDATION, "test": TEST},
                  "series_total": stats.height, "eligible_series": elig.height,
                  "eligible_by_currency": dict(elig.group_by("currency").len().sort("currency").iter_rows()),
                  "panels": {}}

    def sample(seed: int, n: int, exclude_accounts: set | None = None) -> pl.DataFrame:
        pool = elig if not exclude_accounts else elig.filter(~pl.col("account_id").is_in(list(exclude_accounts)))
        idx = np.random.default_rng(seed).permutation(pool.height)[:n]
        return pool[np.sort(idx)].select("account_id", "currency", "train_active_months")

    seeds = CFG["seeds"]
    subsets = {f"seed{s}": sample(s, fc["primary_series"]) for s in seeds["robustness"]}
    subsets["primary"] = subsets.pop(f"seed{seeds['primary']}")
    subsets["disjoint"] = sample(seeds["primary"] + 1000, fc["account_disjoint_series"],
                                 set(subsets["primary"]["account_id"].to_list()))
    for name, keys in subsets.items():
        kp = OUT / f"keys_{name}.parquet"
        keys.write_parquet(kp)
        print(f"panel {name}: {keys.height} series", flush=True)
        rows = int(guarded_child(PANEL_CHILD, str(kp), str(OUT / f"panel_{name}.parquet")))
        meta["panels"][name] = {"series": rows, "accounts": keys["account_id"].n_unique(),
                                "currencies": dict(keys.group_by("currency").len().sort("currency").iter_rows()),
                                "train_active_months_mean": float(keys["train_active_months"].mean())}
    overlap = set(subsets["primary"]["account_id"]) & set(subsets["disjoint"]["account_id"])
    meta["primary_disjoint_account_overlap"] = len(overlap)
    if overlap:
        raise SystemExit("account-disjoint subset overlaps primary")

    an = CFG["anomaly"]
    accounts = pl.read_parquet(ROOT / "data/processed/series_stats/*.parquet", columns=["account_id"]).unique()
    accounts = accounts.sort("account_id")
    idx = np.sort(np.random.default_rng(seeds["primary"]).permutation(accounts.height)[:an["selected_accounts"]])
    sel = accounts[idx]
    sel.write_parquet(OUT / "anomaly_accounts.parquet")
    n_tx = int(guarded_child(ANOMALY_CHILD, str(OUT / "anomaly_accounts.parquet"),
                             str(OUT / "anomaly_transactions.parquet")))
    tx = pl.read_parquet(OUT / "anomaly_transactions.parquet")
    from src.experiments.data_splitting import period_expr
    meta["anomaly"] = {"accounts": sel.height, "transactions": n_tx,
                       "by_period": dict(tx.with_columns(period_expr("month").alias("p"))
                                           .group_by("p").len().sort("p").iter_rows())}
    meta["months"] = {"all": len(ALL_MONTHS)}
    (OUT / "split_metadata.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    print(json.dumps(meta, indent=2, default=str))


if __name__ == "__main__":
    main()
