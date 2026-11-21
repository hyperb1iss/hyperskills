"""Send a batch of messages and report what happened to each one."""

import logging
from dataclasses import dataclass, replace

from . import mailer

log = logging.getLogger(__name__)

SENT = "sent"
FAILED = "failed"
INVALID = "invalid"


@dataclass(frozen=True)
class SendResult:
    key: str
    status: str
    detail: str = ""


def send_batch(transport, batch):
    """Send each ``(key, message)`` pair and return one SendResult per pair, in order.

    ``key`` is the caller's name for the message, such as a user id. A relay
    failure marks that message failed and the rest of the batch still goes out.
    """
    results = []
    for key, message in batch:
        address = mailer.parse_address(message.to)
        try:
            transport.send(replace(message, to=address))
        except mailer.TransportError as exc:
            log.warning("message for %s not sent: %s", key, exc)
            results.append(SendResult(key, FAILED, str(exc)))
            continue
        results.append(SendResult(key, SENT))
    return results
