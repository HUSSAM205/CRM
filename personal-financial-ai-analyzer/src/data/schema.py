"""Canonical transaction schema shared by the dataset pipeline and user CSV uploads.

The schema is taken from the dataset card (HW1 Table 4.2 / HW2 Table 4.2) and was confirmed
against the actual Parquet schema in reports/verification/dataset_integrity_report.md.
"""
from __future__ import annotations

import polars as pl

from src.utils.configuration import load_config

_CFG = load_config("dataset")

REQUIRED_COLUMNS: list[str] = list(_CFG["expected_columns"])

# Physical types observed in the source Parquet file (verified, not assumed).
SOURCE_DTYPES: dict[str, pl.DataType] = {
    "transaction_id": pl.String,
    "account_id": pl.String,
    "transaction_type": pl.String,
    "amount": pl.Float64,
    "currency": pl.String,
    "merchant_category": pl.String,
    "balance_after": pl.Float64,
    "transaction_timestamp": pl.String,
    "status": pl.String,
}

DATASET_CURRENCIES: frozenset[str] = frozenset(_CFG["allowed"]["currencies"])   # the 6 codes of Dataset A
# Uploads may use any active ISO 4217 currency (master audit M-12: TRY and others were rejected because only the
# dataset's 6 codes were allowed). Non-currency codes (XXX "no currency", XTS test, precious metals, XDR/XSU/XUA
# and bond units) are excluded. Amounts are never converted or combined across currencies.
ISO_4217_ACTIVE = frozenset("""
AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD CAD CDF CHF
CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF
IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK
MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR
SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD UYU UZS VES
VND VUV WST XAF XCD XCG XOF XPF YER ZAR ZMW ZWG
""".split())
ALLOWED_CURRENCIES: frozenset[str] = ISO_4217_ACTIVE | DATASET_CURRENCIES
ALLOWED_STATUSES: frozenset[str] = frozenset(_CFG["allowed"]["statuses"])
KNOWN_TRANSACTION_TYPES: frozenset[str] = frozenset(_CFG["allowed"]["transaction_types"])

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
UNCATEGORIZED = "Uncategorized"

# Columns a user CSV must provide (after mapping). Others have documented defaults.
USER_REQUIRED = ["transaction_timestamp", "amount", "currency"]
USER_OPTIONAL_DEFAULTS = {
    "transaction_id": None,          # generated deterministically if absent
    "account_id": "user-account",
    "transaction_type": None,        # derived from amount sign if absent
    "merchant_category": UNCATEGORIZED,
    "status": None,                  # user must confirm "all completed" if absent
    "balance_after": None,           # never used in calculations
}
