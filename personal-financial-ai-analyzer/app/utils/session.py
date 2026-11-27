"""Per-browser-session state, retention and deletion (HW1 F9, 3.2.4; HW2 6.5).

* Uploaded data lives ONLY in this Streamlit session's memory (st.session_state); it is never written
  to disk, never added to the training data, and never sent anywhere.
* Each browser session has its own state, so users cannot see each other's data.
* Retention: the user picks how long data may stay (or "until I close the tab"); expired data is purged
  on the next interaction. "Delete my data now" purges immediately.
"""
from __future__ import annotations

import time
import uuid

import streamlit as st

from src.utils.logging import get_logger

log = get_logger("app.session")
RETENTION_CHOICES = {"15 minutes": 15, "1 hour": 60, "Until I close the tab": None}
DATA_KEYS = ("data", "budgets", "assistant_history")


def init() -> None:
    ss = st.session_state
    ss.setdefault("session_id", uuid.uuid4().hex[:12])
    ss.setdefault("retention", "1 hour")
    ss.setdefault("uploader_key", 0)
    ss.setdefault("budgets", {})
    ss.setdefault("assistant_history", [])


def set_data(clean, rejected, summaries, source: str, mapping: dict | None = None) -> None:
    st.session_state["data"] = {"clean": clean, "rejected": rejected, "summaries": summaries, "source": source,
                                "mapping": mapping, "loaded_at": time.time()}
    st.session_state["budgets"] = {}
    log.info("data loaded: source=%s rows=%d rejected=%d", source, clean.height, rejected.height)


def get_data() -> dict | None:
    return st.session_state.get("data")


def purge(reason: str) -> None:
    for k in DATA_KEYS:
        st.session_state.pop(k, None)
    st.session_state["budgets"] = {}
    st.session_state["assistant_history"] = []
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1   # clears the file widget
    log.info("session data purged: reason=%s", reason)


def enforce_retention(now: float | None = None) -> bool:
    """Purge expired data. Returns True if a purge happened."""
    data = get_data()
    minutes = RETENTION_CHOICES.get(st.session_state.get("retention"))
    if data and minutes is not None and (now or time.time()) - data["loaded_at"] > minutes * 60:
        purge("retention expired")
        return True
    return False
