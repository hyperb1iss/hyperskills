"""Transfers and the gateway's answers to them."""

from dataclasses import dataclass

CURRENCIES = frozenset({"USD", "EUR", "GBP", "CAD"})
MAX_REFERENCE_LENGTH = 35


@dataclass(frozen=True)
class Transfer:
    reference: str
    account_id: str
    amount_cents: int
    currency: str = "USD"

    def __post_init__(self):
        if not isinstance(self.amount_cents, int) or self.amount_cents <= 0:
            raise ValueError("amount_cents must be a positive integer")
        if self.currency not in CURRENCIES:
            raise ValueError(f"unsupported currency {self.currency!r}")
        if not 0 < len(self.reference) <= MAX_REFERENCE_LENGTH:
            raise ValueError(f"reference must be 1 to {MAX_REFERENCE_LENGTH} characters")


@dataclass(frozen=True)
class TransferResult:
    gateway_id: str
    status: str
    message_id: str
