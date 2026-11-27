# Sample data attribution

* `demo_transactions.csv`: three accounts from **Free Financial Transactions 50M** by Zia Data Labs (ziadatalabs), CC BY-NC 4.0 (non-commercial). Created by `scripts/prepare_demo_sample.py`.
* `demo_personaledger.csv`: two users (source IDs 13 and 16) from **PersonaLedger** by Capital One Research (Yuan, Farnan, Tesliuc, Bergman, Wu, Liu, Liu, Montgomery, Nguyen, Bruss, Huang), https://huggingface.co/datasets/capitalone/PersonaLedger, revision `c90078ae4ac47e582c9263579466a905fa4adfab`, licence **CC BY 4.0**.
  * **Changes made:** the schema was mapped to this app's CSV format (amount > 0 → debit; card payment → transfer; other negatives → refund); merchant_type was lower-cased as the category; the currency was labelled "USD" for display, because the source states no currency.
  * Created by `scripts/prepare_personaledger_demo.py`.
* `sample_bank_export.csv` and `tests/fixtures/*`: hand-written by the project author.

Both demo files are fully synthetic. They contain no real person's data.
