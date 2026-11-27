"""Create the SYNTHETIC personal-finance demo files for the practical walkthrough (master audit 4).

These two files are invented by a seeded generator (seed 20261127). They do not come from any real person and
are NOT academic data. They are not used by any experiment. Purpose: let a user practise the import workflow on
a realistic-looking bank export:

  data/samples/demo_personal_part1.csv : 2025-01 .. 2025-12  (first export)
  data/samples/demo_personal_part2.csv : 2025-11 .. 2026-06  (second export; Nov-Dec 2025 OVERLAP part 1)

Format of a typical bank export: Date (with time), Description, Category, signed Amount, Currency (TRY).
No status or type column: the user confirms "all completed"; negative = spending, positive = money received.
Contents: monthly salary (raise in 2026), rent, electricity, internet, Netflix and gym subscriptions, weekly
groceries, metro top-ups, dining that rises in the last three months, and one large electronics purchase at
03:12 (an unusual amount at an unusual hour) in 2026-05.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/samples"
SEED = 20261127


def months(start: tuple[int, int], end: tuple[int, int]):
    y, m = start
    while (y, m) <= end:
        yield y, m
        y, m = (y + (m == 12), 1 if m == 12 else m + 1)


def ts(y: int, m: int, d: int, h: int, mi: int) -> str:
    return datetime(y, m, d, h, mi).strftime("%Y-%m-%d %H:%M:%S")   # noqa: DTZ001 - local bank time, as exported


def month_rows(rng: random.Random, y: int, m: int) -> list[list[str]]:
    rows = []
    salary = 48000.00 if y >= 2026 else 45000.00
    rows.append([ts(y, m, 1, 9, 5), "Salary ACME Teknoloji", "income", f"{salary:.2f}"])
    rows.append([ts(y, m, 2, 10, 15), "Rent payment", "housing", "-17500.00"])
    rows.append([ts(y, m, 5, 7, 40), "FitLife gym subscription", "subscription", "-750.00"])
    rows.append([ts(y, m, 12, 20, 30), "Netflix subscription", "subscription", "-229.99"])
    rows.append([ts(y, m, 18, 11, 0), "Internet bill", "utilities", "-449.90"])
    elec = 900 + (350 if m in (1, 2, 7, 8, 12) else 0) + rng.randint(-60, 60)
    rows.append([ts(y, m, 20, 12, 10), "Electric bill", "utilities", f"-{elec:.2f}"])
    for d in (3, 10, 17, 24):
        rows.append([ts(y, m, d, rng.randint(17, 20), rng.randint(0, 59)), "Migros supermarket", "groceries",
                     f"-{rng.randint(900, 1600) + rng.randint(0, 99) / 100:.2f}"])
    for d in (1, 15):
        rows.append([ts(y, m, d, 8, rng.randint(0, 30)), "Metro card top-up", "transport", "-600.00"])
    recent = (y, m) >= (2026, 4)                     # dining rises in the last three months
    for _ in range(rng.randint(7, 10) if recent else rng.randint(3, 5)):
        d = rng.randint(1, 28)
        rows.append([ts(y, m, d, rng.randint(12, 22), rng.randint(0, 59)), "Restaurant", "dining",
                     f"-{rng.randint(300, 900) + rng.randint(0, 99) / 100:.2f}"])
    if rng.random() < 0.5:
        rows.append([ts(y, m, rng.randint(1, 28), rng.randint(10, 19), rng.randint(0, 59)), "Pharmacy",
                     "healthcare", f"-{rng.randint(150, 600)}.00"])
    if (y, m) == (2026, 5):
        rows.append([ts(2026, 5, 20, 3, 12), "TechStore electronics", "retail", "-24999.00"])
    return sorted(rows)


def main() -> None:
    rng = random.Random(SEED)
    by_month = {ym: month_rows(rng, *ym) for ym in months((2025, 1), (2026, 6))}
    head = ["Date", "Description", "Category", "Amount", "Currency"]
    parts = {"demo_personal_part1.csv": list(months((2025, 1), (2025, 12))),
             "demo_personal_part2.csv": list(months((2025, 11), (2026, 6)))}
    for name, ms in parts.items():
        with (OUT / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(head)
            for ym in ms:
                for r in by_month[ym]:
                    w.writerow([*r, "TRY"])
        print(name, sum(len(by_month[ym]) for ym in ms), "rows")


if __name__ == "__main__":
    main()
