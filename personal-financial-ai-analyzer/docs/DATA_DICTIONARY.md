# Data Dictionary

## Source columns (verified schema)
| Column | Type | Use in this project |
|---|---|---|
| transaction_id | string | Deduplication key; ledger order (numeric part). Not a feature |
| account_id | string | Grouping and splitting only. Not a feature |
| transaction_type | string | Mapped to a meaning (`configs/financial_rules.yaml`) |
| amount | double | Non-negative magnitude. Converted to `amount_cents` (Int64) |
| currency | string | One of six codes. Part of every aggregation key |
| merchant_category | string | One of 14 categories; "Uncategorized" fallback for uploads |
| balance_after | double | **Not used** (D-03) |
| transaction_timestamp | string → datetime | `YYYY-MM-DD HH:MM:SS`. Gives `month`, hour and weekday |
| status | string | Only `completed` counts in totals |

## Derived columns
`amount_cents`, `month`, `meaning`, and in summaries: `income_cents`, `outflow_cents`, `fee_cents`, `refund_cents`, `transfer_cents`, `expenses_cents`, `net_cash_flow_cents`, `completed_records`, `excluded_status_records`, `unresolved_type_records`. Category tables add `gross_spending_cents`, `refund_cents`, `net_spending_cents`. Definitions are in `docs/FINANCIAL_RULES.md`.
