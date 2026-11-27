"""One-command, resumable end-to-end pipeline.

    python scripts/run_full_pipeline.py              # run every step whose outputs are missing
    python scripts/run_full_pipeline.py --force train_forecasting train_anomaly

Steps run in order; a step is skipped when its "done" check passes (so an interrupted run resumes),
unless named in --force. Heavy steps run under the memory guard (configs/resource_limits.yaml).
Each step's outcome is appended to logs/execution/pipeline_runs.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.resource_monitor import run_guarded  # noqa: E402

PY = sys.executable
STEPS = [
    ("download", [PY, "scripts/download_dataset.py"], lambda: (ROOT / "data/raw/PROVENANCE.json").exists()),
    ("verify_dataset", [PY, "scripts/verify_dataset.py"], lambda: (ROOT / "reports/verification/dataset_integrity.json").exists()),
    ("audit", [PY, "scripts/run_audit.py"], lambda: (ROOT / "reports/data_audit/dataset_overview.json").exists()),
    ("ledger", [PY, "scripts/investigate_ledger.py"], lambda: (ROOT / "reports/verification/ledger_semantics.json").exists()),
    ("preprocessing", [PY, "scripts/run_preprocessing.py"], lambda: (ROOT / "data/processed/splits/split_metadata.json").exists()),
    ("demo_sample", [PY, "scripts/prepare_demo_sample.py"], lambda: (ROOT / "data/samples/demo_transactions.csv").exists()),
    ("train_forecasting", [PY, "scripts/train_forecasting.py"], lambda: (ROOT / "reports/experiments/forecasting/summary.json").exists()),
    ("train_anomaly", [PY, "scripts/train_anomaly.py"], lambda: (ROOT / "reports/experiments/anomaly/summary.json").exists()),
    ("evaluate", [PY, "scripts/evaluate_models.py"], lambda: (ROOT / "reports/evaluation/forecasting_error_analysis.json").exists()),
    ("verify_artifacts", [PY, "scripts/verify_artifacts.py"], lambda: False),
    ("tests", [PY, "scripts/run_all_tests.py"], lambda: False),
    ("final_evidence", [PY, "scripts/generate_final_evidence.py"], lambda: False),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", nargs="*", default=[], help="step names to rerun even if done")
    ap.add_argument("--only", nargs="*", default=None, help="run only these steps")
    args = ap.parse_args()
    log = ROOT / "logs/execution/pipeline_runs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    for name, cmd, done in STEPS:
        if args.only is not None and name not in args.only:
            continue
        if done() and name not in args.force:
            print(f"[skip] {name} (outputs present)")
            continue
        print(f"[run ] {name}: {' '.join(cmd[1:])}", flush=True)
        t0 = time.time()
        g = run_guarded(cmd, cwd=ROOT)
        rec = {"step": name, "ok": g.ok, "seconds": round(time.time() - t0, 1), "peak_rss_gb": g.peak_rss_gb,
               "killed_reason": g.killed_reason, "finished_utc": datetime.now(timezone.utc).isoformat()}
        with log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[{'ok' if g.ok else 'FAIL'}] {name} {rec['seconds']}s peak={g.peak_rss_gb}GB", flush=True)
        if not g.ok:
            print(g.stdout_tail[-1500:], g.stderr_tail[-3000:], sep="\n")
            raise SystemExit(f"step '{name}' failed; fix and rerun (completed steps are kept)")


if __name__ == "__main__":
    main()
