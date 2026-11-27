"""Resumable HTTP download and SHA-256 hashing (used by scripts/download_dataset.py)."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests

CHUNK = 8 * 1024 * 1024


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path, expected_size: int, retries: int = 8) -> None:
    """Download to `<dest>.part` with HTTP Range resume; rename only when the size is complete."""
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        if have == expected_size:
            break
        headers = {"Range": f"bytes={have}-"} if have else {}
        print(f"[download] attempt {attempt}: resuming at {have:,} / {expected_size:,} bytes", flush=True)
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as r:
                if r.status_code not in (200, 206):
                    raise RuntimeError(f"HTTP {r.status_code}")
                mode = "ab" if r.status_code == 206 else "wb"
                last = time.time()
                with part.open(mode) as f:          # binary ("ab"/"wb"): no encoding
                    for block in r.iter_content(CHUNK):
                        f.write(block)
                        if time.time() - last > 30:
                            print(f"[download] {part.stat().st_size / expected_size:6.1%}", flush=True)
                            last = time.time()
        except Exception as exc:  # network errors: back off and resume (reported, not hidden)
            print(f"[download] error: {exc!r}; retrying", flush=True)
            time.sleep(min(60, 5 * attempt))
    if not part.exists() or part.stat().st_size != expected_size:
        raise SystemExit(f"download incomplete: {part} size mismatch")
    part.replace(dest)          # replace(): also works on Windows if dest exists
