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
    text = (tmp_path / "t.log").read_text(encoding="utf-8")
    assert "1,234.56" not in text and "TX0000000123" not in text and "ACC-000000001" not in text
    assert "[amount]" in text and "[id]" in text


def test_app_never_writes_uploads_to_disk():
    import subprocess
    out = subprocess.run(["grep", "-rnE", r"write_(csv|parquet)|open\(.*['\"]w", str(ROOT / "app")],
                         capture_output=True, text=True).stdout
    assert "write_parquet" not in out and "open(" not in out, out


def test_app_upload_path_refuses_overflowing_file(monkeypatch):
    """M-02 on the app path: app.components.upload.load_bytes must apply the same total-range guard."""
    from app.components import upload
    from src.data.ingestion import IngestionError, suggest_mapping
    stored = []
    monkeypatch.setattr(upload.session, "set_data", lambda *a, **k: stored.append(a))
    rows = "\n".join(f"2026-01-{(i % 28) + 1:02d},-999999999999.99,USD" for i in range(100_000))
    data = ("Date,Amount,Currency\n" + rows + "\n").encode()
    with pytest.raises(IngestionError, match="supported range"):
        upload.load_bytes(data, suggest_mapping(["Date", "Amount", "Currency"]), "t", assume_completed=True)
    assert not stored


UPLOAD_SCRIPT = """
import sys, types
sys.path.insert(0, {root!r})
import streamlit as st
_data = open({path!r}, 'rb').read()
st.file_uploader = lambda *a, **k: types.SimpleNamespace(getvalue=lambda: _data, name={name!r})   # stand-in widget
from app.utils import session
from app.components import upload
session.init()
upload.render()
"""


@pytest.mark.parametrize("fixture,sep", [("data/samples/sample_bank_export.csv", "comma"),
                                         ("tests/fixtures/unmapped_columns.csv", "comma")])
def test_upload_component_previews_detects_format_and_loads(fixture, sep):
    """Regression (master audit M-11): the upload component crashed with NameError (detect_format not
    imported) after the preview was added; AppTest cannot drive st.file_uploader, so a stand-in returns
    the file bytes and the REAL render() code path runs: detection caption, preview table, mapping, load."""
    from streamlit.testing.v1 import AppTest
    root = Path(__file__).resolve().parents[2]
    at = AppTest.from_string(UPLOAD_SCRIPT.format(root=str(root), path=str(root / fixture), name="x.csv"),
                             default_timeout=60).run()
    assert not at.exception, at.exception
    assert any(f"{sep}-separated" in m.value and "Preview of the first rows" in m.value for m in at.markdown)
    assert len(at.dataframe) >= 1                                   # the raw preview table


def _btn(at, label):
    return next(b for b in at.button if b.label == label)


def test_append_keeps_existing_data_and_replace_needs_confirmation():
    """MA3-01 on the real upload component: with data loaded, a new file is ADDED by default (existing records
    kept, already-loaded records skipped); the same file twice is refused; replacing requires an explicit
    confirmation and only then starts over with the new file."""
    from streamlit.testing.v1 import AppTest
    from app.components.upload import REPLACE
    root = Path(__file__).resolve().parents[2]
    script = UPLOAD_SCRIPT.format(root=str(root), path=str(root / "data/samples/sample_bank_export.csv"),
                                  name="bank.csv")
    at = AppTest.from_string(script, default_timeout=60).run()
    _btn(at, "Load demo data").click().run()
    demo_rows = at.session_state["data"]["clean"].height
    assert not at.exception and demo_rows > 0
    # data loaded -> the mode question appears, default = add
    assert at.radio(key="import_mode").value.startswith("Add")
    next(c for c in at.checkbox if c.label.startswith("All rows in this file are completed")).check().run()
    _btn(at, "Validate and load").click().run()
    d = at.session_state["data"]
    bank_rows = d["imports"][-1]["added"]
    assert bank_rows > 0 and d["clean"].height == demo_rows + bank_rows        # nothing replaced
    assert any("Added" in s.value and "already loaded and skipped" in s.value for s in at.success)
    # the same file again is refused as a whole and changes nothing
    _btn(at, "Validate and load").click().run()
    assert any("already imported" in e.value for e in at.error)
    assert at.session_state["data"]["clean"].height == demo_rows + bank_rows
    # replacing: the button stays disabled until the user confirms
    at.radio(key="import_mode").set_value(REPLACE).run()
    assert _btn(at, "Validate and load").disabled
    at.checkbox(key="confirm_replace").check().run()
    assert not _btn(at, "Validate and load").disabled
    _btn(at, "Validate and load").click().run()
    assert at.session_state["data"]["clean"].height == bank_rows               # only the new file remains
    assert not at.exception


def test_completed_confirmation_is_asked_again_for_each_new_file(tmp_path):
    """MA4: ticking 'all rows are completed' for one file must not silently apply to the next file."""
    from streamlit.testing.v1 import AppTest
    root = Path(__file__).resolve().parents[2]
    f2 = tmp_path / "second.csv"
    f2.write_text("Date,Amount,Currency\n2026-02-01,-5.00,USD\n", encoding="utf-8")
    first = AppTest.from_string(UPLOAD_SCRIPT.format(root=str(root), path=str(root / "data/samples/sample_bank_export.csv"),
                                                     name="a.csv"), default_timeout=60).run()
    second = AppTest.from_string(UPLOAD_SCRIPT.format(root=str(root), path=str(f2), name="b.csv"),
                                 default_timeout=60).run()
    k1 = next(c for c in first.checkbox if c.label.startswith("All rows")).key
    k2 = next(c for c in second.checkbox if c.label.startswith("All rows")).key
    assert k1 != k2 and k1.startswith("assume_completed_") and k2.startswith("assume_completed_")
