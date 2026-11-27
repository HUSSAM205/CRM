"""Memory-safety utilities for heavy data jobs (configs/resource_limits.yaml).

Design:
  * Heavy work runs in a CHILD process (one partition per process). When the child exits, the OS
    reclaims all of its memory, including memory a native allocator would otherwise retain; this is
    the root-cause fix for the RSS growth measured in the first ledger run (3.7 GB -> 12.1 GB over
    20 partitions inside one process).
  * The parent samples the child's RSS (including grandchildren) and SYSTEM available memory every
    `sample_interval_seconds`, and terminates the child if either limit is breached.
  * Each finished partition writes a checkpoint; reruns skip finished partitions (resumable).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import psutil

from src.utils.configuration import load_config

GB = 1e9


@dataclass
class GuardResult:
    returncode: int | None
    seconds: float
    peak_rss_gb: float
    min_system_available_gb: float
    killed_reason: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    samples: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and self.killed_reason is None


def limits() -> dict:
    return load_config("resource_limits")


def system_snapshot() -> dict:
    vm = psutil.virtual_memory()
    du = psutil.disk_usage(str(Path(__file__).resolve().parents[2]))
    return {"ram_total_gb": round(vm.total / GB, 2), "ram_available_gb": round(vm.available / GB, 2),
            "ram_used_pct": vm.percent, "disk_free_gb": round(du.free / GB, 2),
            "cpu_logical": psutil.cpu_count(), "cpu_percent_1s": psutil.cpu_percent(interval=1.0)}


def _tree_rss(proc: psutil.Process) -> int:
    total = 0
    try:
        procs = [proc, *proc.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0
    for p in procs:
        try:
            total += p.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    return total


def run_guarded(args: list[str], cwd: Path | None = None, env_extra: dict | None = None,
                hard_gb: float | None = None, min_avail_gb: float | None = None) -> GuardResult:
    """Run `args` as a child process under memory limits; never raises on a breach."""
    cfg = limits()
    hard = hard_gb if hard_gb is not None else cfg["memory"]["worker_rss_hard_gb"]
    floor = min_avail_gb if min_avail_gb is not None else cfg["memory"]["min_system_available_gb"]
    interval = cfg["memory"]["sample_interval_seconds"]
    env = {**os.environ, "POLARS_MAX_THREADS": str(cfg["parallelism"]["polars_max_threads"]),
           **(env_extra or {})}

    avail0 = psutil.virtual_memory().available / GB
    if avail0 < floor:
        return GuardResult(None, 0.0, 0.0, round(avail0, 2),
                           killed_reason=f"not started: system available {avail0:.2f} GB < {floor} GB")

    t0 = time.time()
    proc = subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    ps = psutil.Process(proc.pid)
    peak, min_avail, reason, n = 0, avail0, None, 0
    while proc.poll() is None:
        rss = _tree_rss(ps)
        avail = psutil.virtual_memory().available / GB
        peak, min_avail, n = max(peak, rss), min(min_avail, avail), n + 1
        if rss / GB > hard:
            reason = f"worker RSS {rss / GB:.2f} GB > hard limit {hard} GB"
        elif avail < floor:
            reason = f"system available {avail:.2f} GB < floor {floor} GB"
        if reason:
            for p in [*ps.children(recursive=True), ps]:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            break
        time.sleep(interval)
    out, err = proc.communicate()
    return GuardResult(proc.returncode, round(time.time() - t0, 2), round(peak / GB, 3),
                       round(min_avail, 2), reason, out[-4000:], err[-4000:], n)


def run_partitions(worker: Path, n_parts: int, checkpoint_dir: Path, log_path: Path,
                   worker_args: list[str] | None = None) -> list[dict]:
    """Run `worker <part> <n_parts> <checkpoint_dir> [args]` for each partition, resumably.

    A partition is complete when its checkpoint `part_XXX.done.json` exists. Stops at the first
    failed or killed partition (completed checkpoints are kept for resume).
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for p in range(n_parts):
        done = checkpoint_dir / f"part_{p:03d}.done.json"
        if done.exists():
            records.append(json.loads(done.read_text(encoding="utf-8")))
            continue
        res = run_guarded([sys.executable, str(worker), str(p), str(n_parts), str(checkpoint_dir),
                           *(worker_args or [])], cwd=worker.parents[1])
        rec = {"partition": p, **asdict(res)}
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({k: v for k, v in rec.items() if k not in ("stdout_tail",)}) + "\n")
        print(f"[part {p + 1}/{n_parts}] ok={res.ok} {res.seconds}s peak_rss={res.peak_rss_gb}GB "
              f"min_sys_avail={res.min_system_available_gb}GB"
              + (f" KILLED: {res.killed_reason}" if res.killed_reason else ""), flush=True)
        if not res.ok:
            print(res.stderr_tail, file=sys.stderr)
            raise SystemExit(f"partition {p} failed; completed checkpoints kept in {checkpoint_dir}")
        done.write_text(json.dumps({k: v for k, v in rec.items() if k not in ("stdout_tail", "stderr_tail")}), encoding="utf-8")
        records.append(rec)
    return records
