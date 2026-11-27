"""Audit A-08 regression: every file the project needs must be tracked by git (a fresh clone must run)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _tracked() -> set[str] | None:
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return set(r.stdout.splitlines()) if r.returncode == 0 else None


@pytest.mark.skipif(_tracked() is None, reason="not a git checkout")
def test_all_source_samples_fixtures_and_artifacts_are_tracked():
    tracked = _tracked()
    required = [p for d in ("src", "app", "scripts", "tests") for p in (ROOT / d).rglob("*.py")
                if "__pycache__" not in p.parts]
    required += list((ROOT / "configs").glob("*.yaml")) + list((ROOT / "tests/fixtures").glob("*"))
    required += list((ROOT / "data/samples").glob("*.csv")) + list((ROOT / "artifacts").rglob("*.json"))
    required += list((ROOT / "artifacts").rglob("*.joblib"))
    required += list(ROOT.glob("*.bat")) + list(ROOT.glob("*.ps1")) + [ROOT / ".streamlit/config.toml"]   # MA4
    missing = sorted(str(p.relative_to(ROOT)) for p in required if str(p.relative_to(ROOT)) not in tracked)
    assert not missing, f"untracked required files: {missing[:20]}"


@pytest.mark.skipif(_tracked() is None, reason="not a git checkout")
def test_dataset_and_derived_data_are_not_tracked():
    tracked = _tracked()
    assert not [t for t in tracked if t.startswith(("data/raw/", "data/processed/", "data/interim/", "data/supplementary/")) and
                not t.endswith("PROVENANCE.json")]
    assert not [t for t in tracked if t.startswith(".venv/")]


def test_windows_batch_files_use_crlf_line_endings():
    """Master audit 3: cmd.exe batch files are stored with CRLF (the repository convention); a rewrite with LF-only
    endings slipped in during this audit and was caught here. Every line must end in CRLF."""
    for bat in sorted(ROOT.glob("*.bat")):
        data = bat.read_bytes()
        assert data.count(b"\n") == data.count(b"\r\n") > 0, bat.name


def test_windows_scripts_call_the_project_entry_points():
    """Static check of the Windows scripts (they cannot be executed here): each uses the project's .venv or
    Python 3.12 and calls an existing script."""
    import re
    for bat in sorted(ROOT.glob("*.bat")):
        text = bat.read_text(encoding="utf-8")
        for script in re.findall(r"scripts\\([\w\\]+\.py)", text):
            assert (ROOT / "scripts" / script.replace("\\", "/")).exists(), (bat.name, script)
        assert ".venv\\Scripts\\python.exe" in text or "-3.12" in text, bat.name
