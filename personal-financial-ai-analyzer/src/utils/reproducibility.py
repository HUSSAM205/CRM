"""Reproducibility helpers: seeds, environment fingerprint, versioned artifact directories."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np

from src.utils.configuration import PROJECT_ROOT, load_config

LIBS = ["polars", "pyarrow", "numpy", "pandas", "scikit-learn", "statsmodels", "joblib", "streamlit", "plotly"]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def fingerprint() -> dict:
    prov = PROJECT_ROOT / "data/raw/PROVENANCE.json"
    p = json.loads(prov.read_text(encoding="utf-8")) if prov.exists() else {}
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "libraries": {lib: version(lib) for lib in LIBS},
            "dataset": {"repo": p.get("dataset"), "revision": p.get("revision_commit"), "sha256": p.get("sha256")}}


def new_artifact_dir(kind: str, model: str, payload_hint: str = "") -> Path:
    """Create artifacts/<kind>/<model>/<version>/ without touching existing versions."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h = hashlib.sha256(f"{stamp}{payload_hint}".encode()).hexdigest()[:8]
    d = PROJECT_ROOT / "artifacts" / kind / model / f"v_{stamp}_{h}"
    d.mkdir(parents=True, exist_ok=False)
    return d


def register(kind: str, model: str, path: Path, role: str) -> None:
    """Record the current version of a model in artifacts/metadata/model_registry.json."""
    reg_path = PROJECT_ROOT / load_config("model_registry")["registry_file"]
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {}
    entry = reg.setdefault(kind, {}).setdefault(model, {"history": []})
    entry["current"] = str(path.relative_to(PROJECT_ROOT))
    entry["role"] = role
    entry["history"].append({"path": entry["current"], "registered_utc": datetime.now(timezone.utc).isoformat()})
    reg_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
