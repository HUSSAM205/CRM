"""Security regression tests (master audit 12): unsafe deserialization paths, markup injection, network
use, error disclosure, upload limits and log redaction. Static checks scan the tracked source."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.utils.formatting import md_escape
from src.data.ingestion import IngestionError, read_csv_bytes

ROOT = Path(__file__).resolve().parents[2]
SRC = [p for d in ("src", "app") for p in (ROOT / d).rglob("*.py")]


@pytest.mark.skipif(not (ROOT / "artifacts/metadata/model_registry.json").exists(), reason="no artifacts")
def test_model_loading_only_from_project_artifacts():
    """joblib (pickle) is only ever loaded from registry paths inside artifacts/ - never from user input."""
    reg = json.loads((ROOT / "artifacts/metadata/model_registry.json").read_text())
    for kind in reg.values():
        for e in kind.values():
            p = (ROOT / e["current"]).resolve()
            assert p.is_relative_to((ROOT / "artifacts").resolve()), e["current"]
    loaders = {str(p.relative_to(ROOT)) for p in SRC if re.search(r"\b(joblib|pickle)\.load\(", p.read_text())}
    assert loaders <= {"src/models/forecasting/inference.py", "src/models/anomaly/anomaly_scoring.py"}, loaders


def test_no_network_or_shell_calls_in_application_code():
    bad = []
    for p in SRC:
        t = p.read_text()
        if p.name != "download.py" and re.search(r"^\s*(import|from)\s+(requests|urllib|httpx|socket|http\.client)\b", t, re.M):
            bad.append(str(p))
        # resource_monitor launches the project's own pipeline workers with a fixed argv (offline pipeline only)
        if p.name != "resource_monitor.py" and re.search(r"\b(os\.system|subprocess\.|eval\(|exec\()", t):
            bad.append(str(p))
    assert not bad, bad


@pytest.mark.parametrize("name", ["../../etc/passwd.csv", "[click](javascript:alert(1)).csv",
                                  "<img src=x onerror=alert(1)>.csv", "**bold**_x_.csv"])
def test_malicious_names_are_escaped_for_markdown(name):
    out = md_escape(name)
    for ch in "[]()<>*_":
        assert ch not in out.replace("\\" + ch, "")      # every special character is escaped


def test_uploaded_file_names_are_never_used_as_paths():
    """The upload widget's name is display-only: no open()/Path() is built from it anywhere in app/."""
    for p in (ROOT / "app").rglob("*.py"):
        t = p.read_text()
        assert not re.search(r"(open|Path)\([^)]*\b(up|uploaded|file)\.name", t), p


def test_binary_and_empty_uploads_are_controlled():
    """(Oversized files: tests/unit/test_ingestion.py::test_too_large_file_rejected_with_size_message.)"""
    with pytest.raises(IngestionError):
        read_csv_bytes(b"\x00\xff\xfe\x00" * 4)
    with pytest.raises(IngestionError):
        read_csv_bytes(b"")


def test_error_details_are_not_shown_to_users():
    cfg = (ROOT / ".streamlit/config.toml").read_text()
    assert re.search(r'showErrorDetails\s*=\s*"type"', cfg) and re.search(r"gatherUsageStats\s*=\s*false", cfg)


def test_log_redaction_masks_amounts_and_identifiers():
    import logging

    from src.utils.logging import RedactFilter
    rec = logging.LogRecord("x", logging.INFO, "f", 1, "paid %s by %s from %s", ("1,234.56", "TX0012422572", "ACC-000481167"), None)
    RedactFilter().filter(rec)
    assert rec.getMessage() == "paid [amount] by [id] from [id]"
