"""User-facing explanations of rejection reasons (HW2 Table 10.1: rejected rows are explained)."""
from __future__ import annotations

REASONS = {
    "invalid_timestamp": "Date/time could not be read (expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).",
    "invalid_amount": "Amount is not a number.",
    "amount_out_of_range": "Amount is larger than 1,000,000,000,000 and was not accepted.",
    "negative_amount": "Amount is negative but a transaction type was also given (amounts must be magnitudes).",
    "amount_precision": "Amount has more than 2 decimal places.",
    "unknown_currency": "Currency is not an active ISO 4217 code (for example USD, EUR, GBP, TRY).",
    "unknown_status": "Status is not completed, pending, failed or reversed.",
    "duplicate_transaction_id": "Same transaction ID as an earlier row; the first one was kept.",
    "already_loaded": "This transaction is already loaded (same account and transaction ID); it was not added again.",
}


def explain(reason: str) -> str:
    if reason.startswith("missing_"):
        return f"Required value '{reason.removeprefix('missing_')}' is empty."
    return REASONS.get(reason, reason)
