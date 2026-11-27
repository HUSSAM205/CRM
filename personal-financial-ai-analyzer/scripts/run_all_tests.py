"""Run the full pytest suite and keep a timestamped log in logs/testing/."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
log = ROOT / "logs/testing" / f"pytest_{stamp}.log"
log.parent.mkdir(parents=True, exist_ok=True)
r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-v", "-p", "no:cacheprovider", *sys.argv[1:]],
                   cwd=ROOT, capture_output=True, text=True)
log.write_text(r.stdout + r.stderr)
(ROOT / "logs/testing/latest.log").write_text(r.stdout + r.stderr)
print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-2000:])
print(f"log: {log.relative_to(ROOT)}")
raise SystemExit(r.returncode)
