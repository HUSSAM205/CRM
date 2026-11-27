"""Refund policy (HW2 5.2: "Refunds reduce the spending of their category").

The dataset has no link from a refund to its original purchase, so a completed refund reduces
spending of the SAME account, currency, merchant_category and calendar month in which the refund
is recorded. Net category spending can therefore be negative in a month where refunds exceed
purchases; it is reported as-is (never clipped) so totals stay reconcilable.
"""
from __future__ import annotations

REFUND_SCOPE = ("account_id", "currency", "merchant_category", "month")
CLIP_NEGATIVE_NET_SPENDING = False
