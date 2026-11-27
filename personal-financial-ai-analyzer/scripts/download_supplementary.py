"""Download Dataset B (PersonaLedger, Capital One Research, CC BY 4.0) at a pinned revision and verify each
file's SHA-256 against the official LFS hash. Files go to data/supplementary/ (git-ignored). Resumable."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REV = "c90078ae4ac47e582c9263579466a905fa4adfab"
FILES = {"raw_generation/normal/transactions.parquet": (228799118, "8ec0979c4e578638e81a2665bae9a4a4604675c10cee41578a7377385425ccb5"),
         "identity_theft_1months/test.parquet": (46761770, "d68c03e8351c1490ddcf1189b0af69fec997a49f9e541e1b180c958fccd3fe63")}


def main() -> int:
    ok = True
    for rel, (size, sha) in FILES.items():
        dst = ROOT / "data/supplementary/personaledger" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_size != size:
            url = f"https://huggingface.co/datasets/capitalone/PersonaLedger/resolve/{REV}/{rel}"
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                tmp = dst.with_suffix(".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                tmp.replace(dst)
        h = hashlib.sha256(dst.read_bytes()).hexdigest()
        good = h == sha and dst.stat().st_size == size
        ok &= good
        print("PASS" if good else "FAIL", rel, dst.stat().st_size, h)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
