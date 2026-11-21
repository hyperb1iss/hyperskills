"""Errors raised by the payouts client."""


class PayoutError(Exception):
    """Base class for payout failures."""


class Rejected(PayoutError):
    """The gateway refused the transfer; sending it again will not help."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class TransientError(PayoutError):
    """The attempt failed in a way that may succeed if repeated."""


class GatewayUnavailable(TransientError):
    """The gateway cannot take messages right now."""


class GatewayTimeout(TransientError):
    """No reply arrived in time. The gateway may or may not have applied the message."""
