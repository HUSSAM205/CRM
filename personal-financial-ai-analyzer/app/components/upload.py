"""CSV upload with schema confirmation and column mapping (HW1 F1, S9; HW2 5.1 steps 1-2)."""
from __future__ import annotations

import streamlit as st

from app.utils import session
from app.utils.formatting import md_escape
from src.analytics.aggregation import build_summaries
from src.data.ingestion import (
    SYNONYMS,
    IngestionError,
    detect_format,
    ingest,
    read_csv_bytes,
    suggest_mapping,
)
from src.data.merge import DuplicateImportError, file_fingerprint
from src.data.schema import ALLOWED_CURRENCIES
from src.data.validation import TotalOutOfRangeError
from src.utils.configuration import PROJECT_ROOT

DEMO_FILE = PROJECT_ROOT / "data/samples/demo_transactions.csv"
DEMO_B_FILE = PROJECT_ROOT / "data/samples/demo_personaledger.csv"     # Dataset B sample (CC BY 4.0), D-24
LABELS = {"transaction_timestamp": "Date / time *", "amount": "Amount *", "currency": "Currency *",
          "transaction_type": "Transaction type", "status": "Status", "merchant_category": "Category",
          "description": "Description (used for keyword categories)", "transaction_id": "Transaction ID",
          "account_id": "Account"}


APPEND, REPLACE = "Add to the loaded transactions", "Replace the loaded transactions"


def load_bytes(data: bytes, mapping: dict, source: str, mode: str = REPLACE, **kw) -> dict | None:
    """Validate a file and load it. mode=APPEND keeps the loaded data and skips records that are already
    loaded (MA3-01); mode=REPLACE (only after the user confirmed it in the UI) starts over with this file."""
    res, _ = ingest(data, mapping, **kw)          # same path as the tests: validation + total-range guard (M-02)
    if res.clean.is_empty():
        raise IngestionError("No valid rows remained after validation; see the reasons below.")
    fp = file_fingerprint(data)
    if mode == APPEND and session.get_data() is not None:
        try:
            return session.append_data(res.clean, res.rejected, source, fingerprint=fp)
        except (DuplicateImportError, TotalOutOfRangeError) as e:
            raise IngestionError(str(e)) from e
    session.set_data(res.clean, res.rejected, build_summaries(res.clean), source, mapping, fingerprint=fp)
    return None


def _mode() -> tuple[str, bool]:
    """When data is already loaded, the user chooses explicitly: add (default, safe) or replace (confirmed)."""
    if session.get_data() is None:
        return REPLACE, True
    mode = st.radio("Transactions are already loaded. What should happen with the next file?", [APPEND, REPLACE],
                    key="import_mode", horizontal=True,
                    help="Adding keeps everything already loaded and skips transactions that are already there. "
                         "Replacing removes the loaded transactions and the budgets based on them.")
    if mode == APPEND:
        return mode, True
    ok = st.checkbox("I understand that replacing removes the loaded transactions and budgets from this session.",
                     key="confirm_replace")
    if not ok:
        st.warning("Confirm the replacement above, or choose 'Add to the loaded transactions'.")
    return mode, ok


def _report(rec: dict | None) -> None:
    if rec is not None:
        st.session_state["last_import"] = rec


def render() -> None:
    st.subheader("Load transactions")
    st.caption("Your file is processed in this browser session only. It is never saved to disk, never used "
               "for training, and never sent to any external service.")
    last = st.session_state.pop("last_import", None)
    if last:
        st.success(f"Added {last['added']:,} new transaction(s) from {md_escape(last['source'])}; "
                   f"{last['already_loaded']:,} were already loaded and skipped; {last['rejected']:,} row(s) of the "
                   "file were rejected (listed below).")
    mode, allowed = _mode()
    c1, c2 = st.columns([3, 1])
    with c2:
        for label, path, src, tip in (
                ("Load demo data", DEMO_FILE, "demo (public synthetic dataset)",
                 "Three synthetic accounts from the public dataset"),
                ("Load PersonaLedger demo", DEMO_B_FILE, "demo (PersonaLedger, CC BY 4.0)",
                 ("Two synthetic card users from PersonaLedger (Capital One Research, CC BY 4.0); continuous "
                  "monthly spending"))):
            if path.exists() and st.button(label, help=tip, disabled=not allowed):
                data = path.read_bytes()
                try:
                    _report(load_bytes(data, suggest_mapping(read_csv_bytes(data).columns), src, mode))
                    st.rerun()
                except IngestionError as e:
                    st.error(str(e))
    with c1:
        up = st.file_uploader("Upload a CSV export", type=["csv"], key=f"uploader_{st.session_state['uploader_key']}")
    if up is None:
        return
    data = up.getvalue()
    try:
        df = read_csv_bytes(data)
    except IngestionError as e:
        st.error(str(e))
        return
    fmt = detect_format(data)
    sep = {"\t": "tab", ",": "comma", ";": "semicolon", "|": "pipe"}[fmt["delimiter"]]
    st.write(f"Detected {df.height:,} rows and {len(df.columns)} columns (encoding {fmt['encoding']}, "
             f"{sep}-separated). Preview of the first rows as read, before any validation:")
    st.dataframe(df.head(5), hide_index=True, width="stretch")
    st.write("Confirm the column mapping:")
    guess = suggest_mapping(df.columns)
    options = ["(not in file)"] + df.columns
    mapping, cols = {}, st.columns(3)
    for i, field in enumerate(SYNONYMS):
        with cols[i % 3]:
            choice = st.selectbox(LABELS[field], options, index=options.index(guess[field]) if guess[field] else 0,
                                  key=f"map_{field}")
            mapping[field] = None if choice == "(not in file)" else choice
    default_currency = None
    if not mapping["currency"]:
        default_currency = st.selectbox("Currency for all rows", sorted(ALLOWED_CURRENCIES), key="default_ccy")
    assume_completed = False
    if not mapping["status"]:
        # keyed per file: the confirmation applies to THIS file only and is asked again for the next one (MA4)
        assume_completed = st.checkbox("All rows in this file are completed (posted) transactions",
                                       key=f"assume_completed_{file_fingerprint(data)[:16]}")
    if not mapping["transaction_type"]:
        st.info("No transaction type column: negative amounts are treated as spending (debit) and positive "
                "amounts as money received (credit). Transfers cannot be detected without a type column.")
    if st.button("Validate and load", type="primary", disabled=not allowed):
        try:
            _report(load_bytes(data, mapping, f"upload: {up.name}", mode, assume_completed=assume_completed,
                               default_currency=default_currency))
            st.rerun()
        except IngestionError as e:
            st.error(str(e))
