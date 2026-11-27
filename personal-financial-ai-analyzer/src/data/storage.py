"""Locations of derived datasets and readers for partitioned tables (configs/preprocessing.yaml)."""
from __future__ import annotations

import polars as pl

from src.utils.configuration import PROJECT_ROOT, load_config

RAW = PROJECT_ROOT / load_config("dataset")["paths"]["raw_parquet"]
OUTPUTS = {k.removesuffix("_dir"): PROJECT_ROOT / v for k, v in load_config("preprocessing")["outputs"].items()}
SPLITS = PROJECT_ROOT / load_config("experiments")["outputs"]["splits_dir"]


def scan_partitioned(name: str) -> pl.LazyFrame:
    """Lazy scan over all partition files of a derived table, e.g. 'monthly', 'monthly_category'."""
    return pl.scan_parquet(OUTPUTS[name] / "part_*.parquet")


def available() -> dict[str, bool]:
    return {"raw": RAW.exists(), **{k: any(v.glob("part_*.parquet")) for k, v in OUTPUTS.items()},
            "splits": (SPLITS / "split_metadata.json").exists()}
