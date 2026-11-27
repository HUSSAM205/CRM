"""User CSV ingestion and column mapping (HW1 F1, S9; HW2 4.5(8), 5.3, Table 10.1).

Flow: read_csv_bytes -> suggest_mapping (user confirms/edits) -> apply_mapping -> validate_transactions.
Every malformed file ends in a controlled IngestionError (HW1 perf. requirement P1), never a crash.
Uploaded bytes are processed in memory only; nothing is written to disk (HW2 6.5).
"""
from __future__ import annotations

import hashlib
import io
import re

import polars as pl

from src.data.schema import UNCATEGORIZED
from src.data.validation import TotalOutOfRangeError, ValidationResult, check_total_range, validate_transactions

from src.utils.configuration import load_config

MAX_UPLOAD_BYTES = int(load_config("app")["upload"]["max_bytes"])   # HW2 Table 10.1 "very large file"
MAX_ROWS = int(load_config("app")["upload"]["max_rows"])

SYNONYMS: dict[str, list[str]] = {
    "transaction_id": ["transaction_id", "id", "txn_id", "transaction id", "reference", "ref"],
    "account_id": ["account_id", "account", "account id", "acct", "account number"],
    "transaction_type": ["transaction_type", "type", "txn_type", "transaction type"],
    "amount": ["amount", "value", "amt", "transaction amount"],
    "currency": ["currency", "ccy", "currency code"],
    "merchant_category": ["merchant_category", "category", "merchant category"],
    "transaction_timestamp": ["transaction_timestamp", "timestamp", "date", "datetime", "transaction date",
                              "posted", "booking date"],
    "status": ["status", "state"],
    "description": ["description", "merchant", "payee", "details", "narrative", "memo"],
}
REQUIRED = ["transaction_timestamp", "amount", "currency"]

# Transparent keyword rules for files without a category (HW2 5.3). First match wins.
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("groceries", ["grocery", "supermarket", "market", "aldi", "lidl", "migros", "carrefour"]),
    ("dining", ["restaurant", "cafe", "coffee", "pizza", "burger", "bar ", "diner"]),
    ("transport", ["uber", "taxi", "metro", "bus", "train", "fuel", "petrol", "parking"]),
    ("travel", ["airline", "hotel", "airbnb", "booking", "flight"]),
    ("utilities", ["electric", "water", "gas bill", "internet", "phone"]),
    ("subscription", ["netflix", "spotify", "subscription", "prime"]),
    ("healthcare", ["pharmacy", "clinic", "hospital", "doctor", "dental"]),
    ("entertainment", ["cinema", "theatre", "concert", "game"]),
    ("education", ["school", "university", "course", "tuition", "book"]),
    ("insurance", ["insurance"]),
    ("cash", ["atm", "cash"]),
    ("retail", ["store", "shop", "amazon", "mall"]),
]


class IngestionError(ValueError):
    """A file-level problem reported to the user with a clear message."""


ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")     # tried in order; utf-8-sig also strips a UTF-8 BOM
DELIMITERS = (",", ";", "\t", "|")


def detect_format(data: bytes) -> dict:
    """Encoding and delimiter of a CSV export (master audit 5.1). Encodings are tried in a fixed order; the
    delimiter is the candidate that splits the header and the first lines into the same, largest number of
    fields. Returns the UTF-8 bytes to parse plus what was detected, so the UI can show it."""
    if b"\x00" in data[:4096]:
        raise IngestionError("The file looks binary, not like a text CSV export.")
    for enc in ENCODINGS:
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:   # latin-1 decodes any byte string, so this is unreachable; kept for clarity
        raise IngestionError("The file's text encoding could not be read; save it as UTF-8.")
    lines = [ln for ln in text.splitlines()[:20] if ln.strip()]
    best, score = ",", (0, 0)
    for d in DELIMITERS:
        counts = [ln.count(d) for ln in lines]
        if counts and counts[0] > 0:
            sc = (sum(c == counts[0] for c in counts), counts[0])
            if sc > score:
                best, score = d, sc
    return {"encoding": "utf-8" if enc == "utf-8-sig" else enc, "delimiter": best,
            "utf8": text.encode("utf-8")}


def read_csv_bytes(data: bytes) -> pl.DataFrame:
    if not data or not data.strip():
        raise IngestionError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise IngestionError(f"The file is {len(data) / 1e6:.1f} MB; the limit is {MAX_UPLOAD_BYTES / 1e6:.0f} MB. "
                             "Split it into smaller files.")
    fmt = detect_format(data)
    try:
        df = pl.read_csv(io.BytesIO(fmt["utf8"]), separator=fmt["delimiter"], infer_schema=False,
                         truncate_ragged_lines=False)
    except Exception as exc:
        raise IngestionError(f"The file could not be read as CSV ({type(exc).__name__}).") from None
    if df.height == 0:
        raise IngestionError("The file has a header but no rows.")
    if df.height > MAX_ROWS:
        raise IngestionError(f"The file has {df.height:,} rows; the limit is {MAX_ROWS:,}.")
    return df.rename({c: c.strip() for c in df.columns})


def suggest_mapping(columns: list[str]) -> dict[str, str | None]:
    lower = {c.lower().strip(): c for c in columns}
    return {field: next((lower[s] for s in syns if s in lower), None) for field, syns in SYNONYMS.items()}


def categorize(description: str | None) -> str:
    text = f" {(description or '').lower()} "
    for cat, words in KEYWORD_RULES:
        if any(w in text for w in words):
            return cat
    return UNCATEGORIZED


ID_KEY_FIELDS = ("account_id", "transaction_timestamp", "amount", "currency", "transaction_type", "status",
                 "merchant_category", "description")


def generated_ids(m: pl.DataFrame) -> list[str]:
    """Deterministic IDs for files without a transaction ID column (MA3-02).

    ID = hash(content of the canonical fields, k), where k counts earlier rows of the SAME file with identical
    content. The row position is not used, so the same transaction gets the same ID in two overlapping exports
    (duplicate imports are detected), while two genuinely identical purchases in one file stay distinct."""
    cols = [c for c in ID_KEY_FIELDS if c in m.columns]
    keys = m.select(pl.concat_str([pl.col(c).cast(pl.String).str.strip_chars().fill_null("") for c in cols],
                                  separator="|")).to_series().to_list()
    seen: dict[str, int] = {}
    out = []
    for k in keys:
        n = seen.get(k, 0)
        seen[k] = n + 1
        out.append(hashlib.sha256(f"{k}|{n}".encode()).hexdigest()[:16])
    return out


def apply_mapping(df: pl.DataFrame, mapping: dict[str, str | None], assume_completed: bool = False,
                  default_currency: str | None = None, default_account: str = "my-account") -> pl.DataFrame:
    """Rename mapped columns to the canonical schema and apply documented defaults.

    * amount with a sign and no transaction_type: negative -> debit, positive -> credit, amount = |x|
    * no status column: requires assume_completed=True (user confirmation), else IngestionError
    * no category: keyword rules on a description column, otherwise "Uncategorized"
    * no transaction_id: deterministic hash of the row content + occurrence index (generated_ids)
    """
    missing = [f for f in REQUIRED if not mapping.get(f) and not (f == "currency" and default_currency)]
    if missing:
        raise IngestionError(f"Map these required columns first: {', '.join(missing)}.")
    out = {}
    for field, col in mapping.items():
        if col:
            if col not in df.columns:
                raise IngestionError(f"Mapped column '{col}' is not in the file.")
            out[field] = df.get_column(col)
    m = pl.DataFrame(out)
    if "currency" not in m.columns:
        m = m.with_columns(pl.lit(default_currency).alias("currency"))
    if "account_id" not in m.columns:
        m = m.with_columns(pl.lit(default_account).alias("account_id"))
    if "status" not in m.columns:
        if not assume_completed:
            raise IngestionError("The file has no status column. Confirm that all rows are completed "
                                 "(posted) transactions, or map a status column.")
        m = m.with_columns(pl.lit("completed").alias("status"))
    if "transaction_type" not in m.columns:
        amt = pl.col("amount").str.strip_chars().str.replace_all(",", "")
        m = m.with_columns(
            pl.when(amt.str.starts_with("-")).then(pl.lit("debit")).otherwise(pl.lit("credit")).alias("transaction_type"),
            amt.str.strip_prefix("-").str.strip_prefix("+").alias("amount"))
    if "merchant_category" not in m.columns:
        if "description" in m.columns:
            m = m.with_columns(pl.col("description").map_elements(categorize, return_dtype=pl.String)
                               .alias("merchant_category"))
        else:
            m = m.with_columns(pl.lit(UNCATEGORIZED).alias("merchant_category"))
    if "transaction_id" not in m.columns:
        m = m.with_columns(pl.Series("transaction_id", generated_ids(m)))
    ts = pl.col("transaction_timestamp").str.strip_chars().str.replace(r"^(\d{4}-\d{2}-\d{2})T", "$1 ")
    m = m.with_columns(pl.when(ts.str.contains(r"^\d{4}-\d{2}-\d{2}$")).then(ts + " 00:00:00")
                         .otherwise(ts).alias("transaction_timestamp"))
    return m.drop("description", strict=False)


def ingest(data: bytes, mapping: dict[str, str | None] | None = None, **kw) -> tuple[ValidationResult, dict]:
    df = read_csv_bytes(data)
    mapping = mapping or suggest_mapping(df.columns)
    res = validate_transactions(apply_mapping(df, mapping, **kw))
    try:
        check_total_range(res.clean)
    except TotalOutOfRangeError as e:
        raise IngestionError(f"File refused: {e}.") from e
    return res, mapping


def safe_label(text: str) -> str:
    """Sanitize user-supplied strings for display (no markup injection)."""
    return re.sub(r"[<>`*_\[\]]", "", str(text))[:80]
