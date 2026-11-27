"""Controlled synthetic anomaly injection (HW2 8.4, 10.3; DECISIONS D-09).

Selects `rate` x N of the scored (test-period) records with a seeded RNG and modifies a COPY:
  amount   : amount multiplied by U(5, 10)
  hour     : hour moved to one never seen in the account's history (least-used if all 24 seen)
  category : category changed to the one least used in the account's history (never-seen first)
Scenarios are assigned uniformly at random. Labels and original values are returned in a separate
table; the clean input frame is never modified.
"""
from __future__ import annotations

import numpy as np
import polars as pl

SCENARIOS = ("amount", "hour", "category")


def inject(scored: pl.DataFrame, history: pl.DataFrame, categories: list[str], rate: float,
           seed: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(seed)
    n = max(1, int(round(rate * scored.height)))
    chosen = np.sort(rng.choice(scored.height, size=n, replace=False))
    scen = rng.choice(len(SCENARIOS), size=n)
    hist_hours = (history.group_by("account_id")
                         .agg(pl.col("transaction_timestamp").dt.hour().alias("h")))
    hours = dict(zip(hist_hours["account_id"], hist_hours["h"].to_list()))
    hist_cats = history.group_by("account_id", "merchant_category").len()
    cat_counts: dict[str, dict[str, int]] = {}
    for a, c, k in hist_cats.iter_rows():
        cat_counts.setdefault(a, {})[c] = k

    rows = scored.with_row_index("_i")
    amt = rows["amount"].to_numpy().copy()
    ts = rows["transaction_timestamp"].to_list()
    cat = rows["merchant_category"].to_list()
    acc = rows["account_id"].to_list()
    labels = []
    for i, s in zip(chosen, scen):
        name = SCENARIOS[s]
        orig = {"amount": float(amt[i]), "hour": ts[i].hour, "category": cat[i]}
        if name == "amount":
            amt[i] = round(amt[i] * rng.uniform(5, 10), 2)
        elif name == "hour":
            seen = hours.get(acc[i], [])
            counts = np.bincount(np.array(seen, dtype=int), minlength=24) if seen else np.zeros(24)
            others = [h for h in range(24) if h != ts[i].hour]          # exclude the current hour FIRST,
            least = min(counts[h] for h in others)                      # then take the least-used of the rest
            cand = [h for h in others if counts[h] == least]
            ts[i] = ts[i].replace(hour=int(rng.choice(cand)))
        else:
            cc = cat_counts.get(acc[i], {})
            least = min(cc.get(c, 0) for c in categories if c != cat[i])
            cand = [c for c in categories if c != cat[i] and cc.get(c, 0) == least]
            cat[i] = str(rng.choice(cand))
        labels.append({"transaction_id": rows["transaction_id"][int(i)], "scenario": name,
                       "original_amount": orig["amount"], "original_hour": orig["hour"],
                       "original_category": orig["category"]})
    modified = scored.with_columns(pl.Series("amount", amt), pl.Series("transaction_timestamp", ts),
                                   pl.Series("merchant_category", cat))
    if "amount_cents" in modified.columns:   # keep the exact-cents column consistent; never add columns
        modified = modified.with_columns((pl.col("amount") * 100).round(0).cast(pl.Int64).alias("amount_cents"))
    return modified, pl.DataFrame(labels)
