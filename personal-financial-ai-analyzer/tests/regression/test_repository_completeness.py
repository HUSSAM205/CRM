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
    missing = sorted(str(p.relative_to(ROOT)) for p in required if str(p.relative_to(ROOT)) not in tracked)
    assert not missing, f"untracked required files: {missing[:20]}"


@pytest.mark.skipif(_tracked() is None, reason="not a git checkout")
def test_dataset_and_derived_data_are_not_tracked():
    tracked = _tracked()
    assert not [t for t in tracked if t.startswith(("data/raw/", "data/processed/", "data/interim/")) and
                not t.endswith("PROVENANCE.json")]
    assert not [t for t in tracked if t.startswith(".venv/")]
