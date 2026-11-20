"""Client for submitting payouts to the gateway."""

import logging
import time
from datetime import datetime, timezone

from .errors import PayoutError, TransientError
from .messages import parse_reply, transfer_message
from .retry import RetryPolicy

log = logging.getLogger(__name__)


def _utcnow():
    return datetime.now(timezone.utc)


class PayoutClient:
    def __init__(self, transport, clock=_utcnow, retry=None, sleep=time.sleep):
        self._transport = transport
        self._clock = clock
        self._retry = retry if retry is not None else RetryPolicy()
        self._sleep = sleep

    def submit(self, transfer):
        """Send ``transfer`` to the gateway and return its TransferResult.

        Transient failures are retried with backoff; Rejected is raised at once.
        """
        # Retrying is safe: every attempt carries the same message_id, and
        # the gateway applies a given message_id at most once.
        message = transfer_message(transfer, sent_at=self._clock())
        attempt = 1
        while True:
            try:
                reply = self._transport.send(message)
            except TransientError as exc:
                if attempt >= self._retry.max_attempts:
                    raise
                delay = self._retry.delay_after(attempt)
                log.warning(
                    "transfer %s attempt %d failed (%s); retrying in %.1fs",
                    transfer.reference, attempt, exc, delay,
                )
                self._sleep(delay)
                attempt += 1
                continue
            return parse_reply(reply)

    def submit_all(self, transfers):
        """Submit each transfer in order. A failed transfer does not stop the rest.

        Returns a dict from reference to TransferResult or the PayoutError raised.
        """
        results = {}
        for transfer in transfers:
            try:
                results[transfer.reference] = self.submit(transfer)
            except PayoutError as exc:
                results[transfer.reference] = exc
        return results
