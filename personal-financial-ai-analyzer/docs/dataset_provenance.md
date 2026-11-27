# Dataset Provenance

## DATASET IDENTITY VERIFIED

Verified 2026-11-27 (UTC). Every value below was measured independently. None was copied from the download script's own output.

| # | Item | Value | Evidence |
|---|---|---|---|
| 1 | Local file path | `personal-financial-ai-analyzer/data/raw/transactions_50M.parquet` (absolute: `/home/user/CRM/personal-financial-ai-analyzer/data/raw/transactions_50M.parquet`) | `realpath` |
| 2 | Size | **1,594,749,644 bytes**: 1.5947 GB (10⁹) or 1.4852 GiB | `stat` |
| 3 | Local SHA-256 | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` | Computed twice with independent tools: coreutils `sha256sum` and Python `hashlib` |
| 4 | Official LFS SHA-256 | `b18c83595d2e7a06598c00a3cbe01eb0586b2f0b10443305c6283586c27f8c17` | HF API `/tree/main` `lfs.oid`, and the `x-linked-etag` header on the official `resolve/main` URL |
| 5 | HF revision | `main` = commit **`98cf38f9b2f1a9994930f52a4d490cb2b5777acc`** (2026-08-16T15:14:02Z). The parquet was added in commit `3a5ad0d0…` (2026-08-16T15:13:59Z), and no later commit touches it. | `x-repo-commit` header, API `/revision/main`, `/commits/main` |
| 6 | Schema | `transaction_id` string, `account_id` string, `transaction_type` string, `amount` double, `currency` string, `merchant_category` string, `balance_after` double, `transaction_timestamp` string, `status` string. Nine columns, matching the dataset card and the order in HW1 and HW2 Table 4.2. | Parquet footer (`scripts/verify_dataset.py`) |
| 7 | Row count | **50,000,000**. The footer total, the sum of 50 row groups of 1,000,000 rows, and an actual read of every row group all agree. | `scripts/verify_dataset.py` |
| 8 | Not a sample or partial | Size equals the official LFS size exactly, the hash matches, and no `.part` file remains. 50 M rows were read. The official sample is a different file (`sample_50rows.csv`, 5,394 bytes), stored separately as `data/external/sample_50rows.csv`. | All of the above |

Raw evidence: `reports/verification/dataset_identity_check.txt` and `reports/verification/dataset_integrity.json`

## Source and license

* Repository: `ziadatalabs/FreeFinancialTransactions50M` (Hugging Face; the dataset card titles it "FreeSyntheticFinancialTransactions50M").
* Official URL: https://huggingface.co/datasets/ziadatalabs/FreeFinancialTransactions50M
* Download URL used, pinned to the commit: `.../resolve/98cf38f9b2f1a9994930f52a4d490cb2b5777acc/transactions_50M.parquet`. It is byte-identical to `resolve/main` on the verification date.
* License: **CC BY-NC 4.0**. Attribution: "Created by Zia Data Labs". Non-commercial use only. This academic project complies.
* Data origin: fully synthetic, according to the dataset card. No real people or accounts.
* Download: 2026-11-27 02:38–02:40 UTC, using `scripts/download_dataset.py` (resumable over HTTP Range, then hash-verified).
* HW1 and HW2 give an access date of 22 Oct 2026. The file has been unchanged on `main` since 2026-08-16, so it is the version available on that date. The HWs did not record a hash, so byte-identity with the student's earlier copy cannot be proven.

## Integrity rules

* `data/raw/` is read-only by convention. No script writes to it except `download_dataset.py`, which refuses to overwrite an existing file and only verifies it.
* The raw file and every derived dataset are excluded from git by `.gitignore`, because of their size.
* To re-verify at any time, run `python scripts/verify_dataset.py`. Its 27 checks are listed in `reports/verification/dataset_integrity_report.md`.
