---
license: cc-by-nc-4.0
task_categories:
- tabular-classification
- time-series-forecasting
language:
- en
tags:
- synthetic-data
- finance
- transactions
- banking
- fintech
size_categories:
- 10M<n<100M
---

# FreeSyntheticFinancialTransactions50M

A free dataset of 50 million fully synthetic banking transactions, built for developers and researchers who need realistic financial ledger data at scale — for testing banking apps, ledger and reconciliation logic, budgeting and personal-finance tools, or transaction-processing pipelines. No real people, accounts, or transactions are represented in this data.

## Schema

| Column | Type | Description |
|---|---|---|
| transaction_id | string | Unique transaction identifier |
| account_id | string | Synthetic account identifier |
| transaction_type | string | debit, credit, transfer, fee, interest, refund, withdrawal, deposit |
| amount | float | Transaction amount |
| currency | string | Currency code (USD, EUR, GBP, CAD, AUD, JPY) |
| merchant_category | string | Spending category (groceries, dining, utilities, etc.) |
| balance_after | float | Running account balance after the transaction |
| transaction_timestamp | string | Transaction time (YYYY-MM-DD HH:MM:SS) |
| status | string | completed, pending, failed, or reversed |

## Format

Single Parquet file, Snappy compression, ~1.5 GB, 50,000,000 rows.

## Quick Start

**pandas**
```python
import pandas as pd
df = pd.read_parquet("transactions_50M.parquet")
```

**datasets**
```python
from datasets import load_dataset
ds = load_dataset("ziadatalabs/FreeSyntheticFinancialTransactions50M")
```

**duckdb**
```python
import duckdb
duckdb.sql("SELECT * FROM 'transactions_50M.parquet' LIMIT 10").show()
```

## Notes

Each account carries a running balance that updates consistently across its completed transactions, so the ledger stays internally coherent for reconciliation testing. Amounts follow a realistic log-normal distribution (mostly small, occasional large), transaction types and statuses follow typical banking proportions, and most transactions are completed with small tails of pending, failed, and reversed. All entirely synthetic.

## License & Usage

Released under CC BY-NC 4.0 — personal, research, and educational use permitted, attribution required, no commercial use.

---

Created by Zia Data Labs. Questions or feedback: zia.data.team@protonmail.com
