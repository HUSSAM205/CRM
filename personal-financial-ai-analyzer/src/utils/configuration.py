"""Load YAML configuration files from the project's configs/ directory."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


@lru_cache(maxsize=None)
def load_config(name: str) -> dict[str, Any]:
    """Return the parsed contents of configs/<name>.yaml."""
    path = CONFIG_DIR / f"{name}.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def project_path(relative: str | Path) -> Path:
    """Resolve a path relative to the project root."""
    return PROJECT_ROOT / relative
