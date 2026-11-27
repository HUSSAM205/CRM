"""User-facing explanations of rejection reasons (HW2 Table 10.1: rejected rows are explained)."""
from __future__ import annotations

REASONS = {
    "invalid_timestamp": "Date/time could not be read (expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).",
    "invalid_amount": "Amount is not a number.",
    "negative_amount": "Amount is negative but a transaction type was also given (amounts must be magnitudes).",
    "amount_precision": "Amount has more than 2 decimal places.",
    "unknown_currency": "Currency is not one of USD, EUR, GBP, CAD, AUD, JPY.",
    "unknown_status": "Status is not completed, pending, failed or reversed.",
    "duplicate_transaction_id": "Same transaction ID as an earlier row; the first one was kept.",
}


def explain(reason: str) -> str:
    if reason.startswith("missing_"):
        return f"Required value '{reason.removeprefix('missing_')}' is empty."
    return REASONS.get(reason, reason)
