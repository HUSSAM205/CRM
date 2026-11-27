"""Peak resident memory of the current process, on Linux, macOS and Windows (master audit 4).

The `resource` module exists only on Unix; on Windows `psutil` reports the peak working set instead.
Units: GB (1e9 bytes). Linux reports ru_maxrss in KiB, macOS in bytes.
"""
from __future__ import annotations

import sys


def peak_rss_gb(ndigits: int = 3) -> float:
    try:
        import resource
    except ImportError:                     # Windows
        import psutil
        return round(psutil.Process().memory_info().peak_wset / 1e9, ndigits)
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(v / 1e9 if sys.platform == "darwin" else v / 1e6, ndigits)
