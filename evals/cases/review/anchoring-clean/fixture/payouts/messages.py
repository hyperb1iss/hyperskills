"""Wire messages for the payout gateway."""

import uuid

from .errors import Rejected
from .models import TransferResult

ACCEPTED_STATUSES = ("accepted", "pending")


def new_message_id():
    return uuid.uuid4().hex


def transfer_message(transfer, sent_at):
    """Build the gateway message that creates ``transfer``."""
    return {
        "message_id": new_message_id(),
        "kind": "transfer.create",
        "sent_at": sent_at.isoformat(),
        "transfer": {
            "reference": transfer.reference,
            "account": transfer.account_id,
            "amount": transfer.amount_cents,
            "currency": transfer.currency,
        },
    }


def parse_reply(reply):
    """Turn a gateway reply into a TransferResult; raise Rejected on refusal."""
    status = reply.get("status")
    if status == "rejected":
        raise Rejected(reply.get("code", "unknown"), reply.get("detail", ""))
    if status not in ACCEPTED_STATUSES:
        raise ValueError(f"unexpected gateway status {status!r}")
    return TransferResult(
        gateway_id=reply["gateway_id"],
        status=status,
        message_id=reply["message_id"],
    )
