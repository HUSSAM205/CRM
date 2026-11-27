# Ledger Semantics Investigation

**Status: PASS, conclusive.** Run 2026-11-27 02:57 UTC over **all 50,000,000 rows and all 1,000,000 accounts**, with no sampling.
Evidence: `reports/verification/ledger_semantics.json`, `ledger_by_transaction_id.csv`, `ledger_by_timestamp.csv`, `logs/execution/investigate_ledger.log`, `logs/execution/ledger_partitions.jsonl`.
Code: `scripts/investigate_ledger.py` (driver), `scripts/workers/ledger_partition.py`, `scripts/workers/id_partition.py`.

## Why this was investigated

Inspecting account `ACC-000532504` in timestamp order showed `balance_after` moving in ways that cannot match the transactions. For example, a 20.39 `fee` was followed by a balance *increase* of 145.82. The dataset card says each account carries "a running balance that updates consistently across its completed transactions". The question was which ordering, if any, makes that statement true.

## Hypothesis and method

H: within one account, ordered by key K, for every record after the account's first:

* `completed` record: Δbalance = direction(type) × amount
* `pending`, `failed` or `reversed` record: Δbalance = 0

with direction(type) = −1 for `debit`, `withdrawal`, `fee`, `transfer` and +1 for `credit`, `deposit`, `interest`, `refund`.

* All arithmetic is in exact integer cents: round(x × 100).
* Two orderings were tested:
  * **K1** = numeric part of `transaction_id`;
  * **K2** = `transaction_timestamp`, with the ID as tie-breaker.
* Each account's first record has no predecessor, so 1,000,000 records are excluded. That leaves 49,000,000 compared records.

## Results

| Measure | Ordered by transaction_id | Ordered by timestamp |
|---|---|---|
| Records matching H | **49,000,000 / 49,000,000 (100.0000%)** | 1,071,037 / 49,000,000 (2.19%) |
| Accounts where every record matches | **1,000,000 / 1,000,000** | 0 / 1,000,000 |

Every one of the 32 (type × status) cells is 100.0% in ID order and 2.1–2.6% in timestamp order (see the CSVs). So H holds without exception for every type and status in ID order.

### Further measured facts

| Fact | Value |
|---|---|
| Accounts whose ID order equals their timestamp order | **0** of 1,000,000 |
| `transaction_id` values unique | 50,000,000 of 50,000,000 |
| Numeric part of ID | unique, and exactly the contiguous range 0 … 49,999,999 |
| IDs in the form `TX` + 10 digits | 49,999,800 |
| IDs with suffix `-zdl26nr51f60aaa959f` | 200 (unique; no bare base ID exists for them) |
| Accounts holding more than one currency under one balance | **1,000,000** (every account) |
| Accounts whose balance goes below 0 at some point | 37,742 |

## Conclusions

1. **The sign convention is established.** `amount` is a non-negative magnitude. Its direction comes from `transaction_type`: `debit`, `withdrawal`, `fee` and `transfer` reduce the balance; `credit`, `deposit`, `interest` and `refund` increase it. This is now measured, not assumed, and `src/rules/transaction_mapping.py::BALANCE_DIRECTION` encodes exactly this.
2. **The status semantics are established.** Only `completed` records change the balance. `pending`, `failed` and `reversed` never do. This independently confirms the HW policy of counting only completed records.
3. **`transaction_id` is a reliable ledger sequence.** Ordering by its numeric part reconciles 100% of records.
4. **Timestamps are not consistent with the ledger sequence.** In no account does time order equal ledger order. The synthetic generator evidently assigned timestamps independently of the balance sequence.
5. **`balance_after` is not a meaningful per-currency quantity.** One running number mixes USD, EUR, JPY and other currencies within the same account.

## Decisions taken (also in DECISIONS.md)

* **D-03.** `balance_after` is **not** used in any financial calculation or predictive feature. This was already required by HW1 Table 4.2 and HW2 4.6 as a leakage risk. The two findings above add independent reasons: it mixes currencies, and it is ordered by ID rather than time.
* **D-04.** All calendar logic (months, splits, lags, hour and day-of-week features) uses `transaction_timestamp`, because it is the only time field. This rests on an assumption the data cannot confirm: that timestamps represent when transactions happened. They are internally consistent, with 0 unparseable values and full coverage from 2024-01-01 to 2026-07-31, but they do not agree with the ledger order. This is recorded in `docs/limitations.md`.
* **D-05.** The 200 suffixed IDs are **kept**. They are unique and break no validation rule. They are flagged in the data-quality report. Their meaning (possibly a provider watermark) is **unknown and not asserted**.
* **D-06.** Transfers reduce the balance, so in this dataset they are outgoing. Whether the destination is the user's own account cannot be determined, because there is no counterparty field. Following HW2 5.2, transfers are kept out of income and expenses and reported separately. This is a documented assumption (CF-08).

## Resource behaviour (for the 16 GB laptop)

* The first single-process version grew from 3.7 GB to 12.1 GB RSS over 20 partitions, even after `del` and `gc`: memory was not returned to the OS within the process.
* The fix is one partition per child process (`src/utils/resource_monitor.py`). Measured peak was **0.81 GB** per worker. System available memory never fell below 14.8 GB of 16.9 GB. Total worker time was 139 s for 50 partitions.
* A single-pass global `n_unique` over 50M IDs exceeded the 4.0 GB hard limit and was **terminated by the guard as designed**. It was replaced by ID-partitioned counting with a 0.25 GB peak. Equal IDs share a numeric part, so the result is exact.
