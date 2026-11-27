"""Logging that never records raw financial values (HW2 6.5).

Messages may contain counts, sources and status words only. A redaction filter masks anything that
looks like a monetary amount or a transaction/account identifier, as a second line of defence.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from src.utils.configuration import PROJECT_ROOT

_MONEY = re.compile(r"(?<![\w.])-?\d{1,3}(?:[,\d]{0,12})\.\d{2}(?!\d)")
_IDS = re.compile(r"\b(?:TX\d{6,}[\w-]*|ACC-\d+)\b")


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        record.msg, record.args = _IDS.sub("[id]", _MONEY.sub("[amount]", msg)), ()
        return True


def get_logger(name: str, logfile: str = "logs/application/app.log") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        path = PROJECT_ROOT / logfile
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(path, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        h.addFilter(RedactFilter())
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
