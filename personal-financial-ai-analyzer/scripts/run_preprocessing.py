"""Gates 4 and 6: build the partitioned aggregate tables, then the experimental splits/subsets."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for script in ("scripts/build_aggregates.py", "scripts/create_splits.py"):
    print(f"== {script}", flush=True)
    if subprocess.run([sys.executable, script], cwd=ROOT).returncode != 0:
        raise SystemExit(f"{script} failed")
