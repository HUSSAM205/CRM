# Dataset Integrity Report

Generated 2026-11-27 03:17 UTC from `reports/verification/dataset_integrity.json` (run 2026-11-27T02:44:21.320755+00:00).
Script: `scripts/verify_dataset.py` (does not trust download-time provenance; re-derives everything).

**Overall: PASS** (27/27 checks). Identity: see `docs/dataset_provenance.md`, **DATASET IDENTITY VERIFIED**.

| Fact | Value |
|---|---|
| File | `data/raw/transactions_50M.parquet` |
| Size | 1,594,749,644 bytes |
| SHA-256 | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` |
| Live HF LFS oid | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` |
| Row groups | 50 (1,000,000–1,000,000 rows each) |
| Rows (footer / actually read) | 50,000,000 / 50,000,000 |
| Writer / compression | parquet-cpp-arrow version 25.0.1 / SNAPPY |
| Timestamp min / max | 2024-01-01 00:00:03 / 2026-07-31 23:59:59 |
| Unparseable timestamps | 0 |

## Checks
| Check | Status | Evidence |
|---|---|---|
| file_exists | **PASS** | `data/raw/transactions_50M.parquet` |
| no_partial_download_left | **PASS** | `none` |
| live_hf_metadata_fetched | **PASS** | `https://huggingface.co/api/datasets/ziadatalabs/FreeFinancialTransactions50M/tree/98cf38f9b2f1a9994930f52a4d490cb2b5777acc` |
| size_matches_config | **PASS** | `1594749644` |
| size_matches_live_hf | **PASS** | `1594749644 vs 1594749644` |
| sha256_matches_live_hf_lfs_oid | **PASS** | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` |
| parquet_footer_readable | **PASS** | `50 row groups, created_by=parquet-cpp-arrow version 25.0.1` |
| column_names_and_order | **PASS** | `['transaction_id', 'account_id', 'transaction_type', 'amount', 'currency', 'merchant_category', 'balance_after', 'transaction_timestamp', 'status']` |
| column_types | **PASS** | `{'transaction_id': 'string', 'account_id': 'string', 'transaction_type': 'string', 'amount': 'double', 'currency': 'string', 'merchant_category': 'string', 'bal` |
| column_count_matches_advertised | **PASS** | `9` |
| footer_rows_equal_sum_row_groups | **PASS** | `50000000` |
| rows_read_equal_footer | **PASS** | `50000000` |
| rows_match_advertised | **PASS** | `50000000` |
| all_timestamps_parse | **PASS** | `0` |
| timestamp_min_on_advertised_start | **PASS** | `2024-01-01 00:00:03` |
| timestamp_max_on_advertised_end | **PASS** | `2026-07-31 23:59:59` |
| currency_count_matches_advertised | **PASS** | `6` |
| currency_values_match_documented | **PASS** | `['AUD', 'CAD', 'EUR', 'GBP', 'JPY', 'USD']` |
| transaction_type_count_matches_advertised | **PASS** | `8` |
| transaction_type_values_match_documented | **PASS** | `['credit', 'debit', 'deposit', 'fee', 'interest', 'refund', 'transfer', 'withdrawal']` |
| status_count_matches_advertised | **PASS** | `4` |
| status_values_match_documented | **PASS** | `['completed', 'failed', 'pending', 'reversed']` |
| merchant_category_count_matches_advertised | **PASS** | `['cash', 'dining', 'education', 'entertainment', 'groceries', 'healthcare', 'insurance', 'other', 'retail', 'subscription', 'transfer', 'transport', 'travel', '` |
| currency_no_null_values | **PASS** | `none` |
| merchant_category_no_null_values | **PASS** | `none` |
| transaction_type_no_null_values | **PASS** | `none` |
| status_no_null_values | **PASS** | `none` |

## Schema (physical)
| Column | Type |
|---|---|
| transaction_id | string |
| account_id | string |
| transaction_type | string |
| amount | double |
| currency | string |
| merchant_category | string |
| balance_after | double |
| transaction_timestamp | string |
| status | string |

## Value domains (full scan, all rows)
* **currency**: AUD (2,499,058), CAD (3,499,177), EUR (9,001,468), GBP (5,000,059), JPY (2,499,646), USD (27,500,592)
* **merchant_category**: cash (3,568,889), dining (3,573,003), education (3,569,242), entertainment (3,577,264), groceries (3,573,561), healthcare (3,572,288), insurance (3,569,356), other (3,572,682), retail (3,571,506), subscription (3,571,534), transfer (3,571,454), transport (3,570,482), travel (3,568,268), utilities (3,570,471)
* **transaction_type**: credit (9,998,728), debit (19,999,177), deposit (2,501,085), fee (3,000,311), interest (1,500,674), refund (2,001,601), transfer (6,999,417), withdrawal (3,999,007)
* **status**: completed (45,999,107), failed (1,250,047), pending (2,250,253), reversed (500,593)
