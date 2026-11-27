"""Resumable, hash-verified download of the FreeFinancialTransactions50M Parquet file.

Pinned to an exact Hugging Face repository commit so the dataset revision is reproducible.
Writes provenance to data/raw/PROVENANCE.json and never modifies an existing verified file.

Usage:
    python scripts/download_dataset.py            # download + verify
    python scripts/download_dataset.py --verify   # only verify an existing file
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.download import download, sha256_of  # noqa: E402
from src.utils.configuration import load_config  # noqa: E402

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="only verify the existing file")
    args = ap.parse_args()

    cfg = load_config("dataset")
    src = cfg["source"]
    dest = ROOT / cfg["paths"]["raw_parquet"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{src['repo_id']}/resolve/{src['revision']}/{src['filename']}"
    started = datetime.now(timezone.utc).isoformat()

    if not dest.exists():
        if args.verify:
            raise SystemExit(f"missing {dest}")
        download(url, dest, int(src["expected_size_bytes"]))

    size = dest.stat().st_size
    print("[verify] computing SHA-256 ...", flush=True)
    digest = sha256_of(dest)
    ok = size == int(src["expected_size_bytes"]) and digest == src["expected_sha256"]
    prov = {
        "dataset": src["repo_id"],
        "source_url": f"https://huggingface.co/datasets/{src['repo_id']}",
        "download_url": url,
        "revision_commit": src["revision"],
        "filename": src["filename"],
        "license": src["license"],
        "local_path": str(dest.relative_to(ROOT)),
        "size_bytes": size,
        "expected_size_bytes": int(src["expected_size_bytes"]),
        "sha256": digest,
        "expected_sha256_lfs_oid": src["expected_sha256"],
        "verified": ok,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_started_at_utc": started,
    }
    (dest.parent / "PROVENANCE.json").write_text(json.dumps(prov, indent=2))
    print(json.dumps(prov, indent=2))
    if not ok:
        raise SystemExit("VERIFICATION FAILED: size or SHA-256 mismatch")
    print("[verify] PASS")


if __name__ == "__main__":
    main()
