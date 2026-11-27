"""Upload, session isolation, retention/deletion and log privacy (HW1 F9, HW2 6.5)."""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data.ingestion import ingest, read_csv_bytes, suggest_mapping
from src.utils.logging import get_logger

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "data/samples/sample_bank_export.csv"

SESSION_SCRIPT = """
import sys
sys.path.insert(0, {root!r})
import streamlit as st
from app.utils import session
session.init()
expired = session.enforce_retention()
st.write("expired" if expired else "kept")
st.write("has_data" if session.get_data() else "no_data")
"""


@pytest.mark.skipif(not BANK.exists(), reason="sample not prepared")
def test_bank_export_sample_maps_and_validates():
    data = BANK.read_bytes()
    m = suggest_mapping(read_csv_bytes(data).columns)
    assert m["transaction_timestamp"] == "Date" and m["amount"] == "Amount" and m["merchant_category"] == "Category"
    res, _ = ingest(data, assume_completed=True)
    assert res.rejected.is_empty() and res.clean.height == read_csv_bytes(data).height
    assert set(res.clean["transaction_type"]) <= {"debit", "credit"}


def _app(**state):
    at = AppTest.from_string(SESSION_SCRIPT.format(root=str(ROOT)))
    for k, v in state.items():
        at.session_state[k] = v
    return at.run()


def test_retention_expiry_purges_data():
    old = {"clean": None, "rejected": None, "summaries": None, "source": "x", "loaded_at": time.time() - 3600}
    at = _app(data=old, retention="15 minutes")
    assert [m.value for m in at.markdown] == ["expired", "no_data"]


def test_retention_until_tab_closed_keeps_data():
    old = {"clean": None, "rejected": None, "summaries": None, "source": "x", "loaded_at": time.time() - 10 ** 6}
    at = _app(data=old, retention="Until I close the tab")
    assert [m.value for m in at.markdown] == ["kept", "has_data"]


def test_sessions_are_isolated():
    a = _app(data={"clean": None, "rejected": None, "summaries": None, "source": "a", "loaded_at": time.time()})
    b = _app()
    assert a.session_state["session_id"] != b.session_state["session_id"]
    assert "data" not in b.session_state


def test_logs_never_contain_amounts_or_ids(tmp_path):
    log = get_logger("test.privacy", logfile=str(tmp_path / "t.log"))
    log.info("loaded %s amount=%s id=%s acct=%s", "x", "1,234.56", "TX0000000123", "ACC-000000001")
    for h in log.handlers:
        h.flush()
    text = (tmp_path / "t.log").read_text()
    assert "1,234.56" not in text and "TX0000000123" not in text and "ACC-000000001" not in text
    assert "[amount]" in text and "[id]" in text


def test_app_never_writes_uploads_to_disk():
    import subprocess
    out = subprocess.run(["grep", "-rnE", r"write_(csv|parquet)|open\(.*['\"]w", str(ROOT / "app")],
                         capture_output=True, text=True).stdout
    assert "write_parquet" not in out and "open(" not in out, out
