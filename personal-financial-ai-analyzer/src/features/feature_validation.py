"""Guard applied before any model is trained or saved: forbidden columns never become features
(docs/leakage_analysis.md L1, L7, L9; DECISIONS D-03)."""
from __future__ import annotations

FORBIDDEN_FEATURES = frozenset({"balance_after", "account_id", "transaction_id"})


class LeakageError(ValueError):
    pass


def assert_allowed(features: list[str]) -> list[str]:
    bad = FORBIDDEN_FEATURES & set(features)
    if bad:
        raise LeakageError(f"forbidden feature(s): {sorted(bad)}")
    if len(set(features)) != len(features):
        raise LeakageError("duplicate feature names")
    return features
