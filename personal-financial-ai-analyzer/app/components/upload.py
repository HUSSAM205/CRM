"""CSV upload with schema confirmation and column mapping (HW1 F1, S9; HW2 5.1 steps 1-2)."""
from __future__ import annotations

import streamlit as st

from app.utils import session
from src.analytics.aggregation import build_summaries
from src.data.ingestion import SYNONYMS, IngestionError, apply_mapping, read_csv_bytes, suggest_mapping
from src.data.schema import ALLOWED_CURRENCIES
from src.data.validation import validate_transactions
from src.utils.configuration import PROJECT_ROOT

DEMO_FILE = PROJECT_ROOT / "data/samples/demo_transactions.csv"
LABELS = {"transaction_timestamp": "Date / time *", "amount": "Amount *", "currency": "Currency *",
          "transaction_type": "Transaction type", "status": "Status", "merchant_category": "Category",
          "description": "Description (used for keyword categories)", "transaction_id": "Transaction ID",
          "account_id": "Account"}


def load_bytes(data: bytes, mapping: dict, source: str, **kw) -> None:
    res = validate_transactions(apply_mapping(read_csv_bytes(data), mapping, **kw))
    if res.clean.is_empty():
        raise IngestionError("No valid rows remained after validation; see the reasons below.")
    session.set_data(res.clean, res.rejected, build_summaries(res.clean), source, mapping)


def render() -> None:
    st.subheader("Load transactions")
    st.caption("Your file is processed in this browser session only. It is never saved to disk, never used "
               "for training, and never sent to any external service.")
    c1, c2 = st.columns([3, 1])
    with c2:
        if DEMO_FILE.exists() and st.button("Load demo data", help="Three synthetic accounts from the public dataset"):
            data = DEMO_FILE.read_bytes()
            df = read_csv_bytes(data)
            load_bytes(data, suggest_mapping(df.columns), "demo (public synthetic dataset)")
            st.rerun()
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
    st.write(f"Detected {df.height:,} rows and {len(df.columns)} columns. Confirm the column mapping:")
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
        assume_completed = st.checkbox("All rows in this file are completed (posted) transactions",
                                       key="assume_completed")
    if not mapping["transaction_type"]:
        st.info("No transaction type column: negative amounts are treated as spending (debit) and positive "
                "amounts as money received (credit). Transfers cannot be detected without a type column.")
    if st.button("Validate and load", type="primary"):
        try:
            load_bytes(data, mapping, f"upload: {up.name}", assume_completed=assume_completed,
                       default_currency=default_currency)
            st.rerun()
        except IngestionError as e:
            st.error(str(e))
