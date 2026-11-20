"""Transport to the payout gateway.

The gateway applies each message_id at most once. When it receives a message
whose message_id it has already applied, it does not apply it again and answers
with the reply it gave the first time. Message ids are remembered for 24 hours.
The gateway stores sent_at for reconciliation only; it never rejects a message
because sent_at is old.
"""

from .errors import GatewayTimeout, GatewayUnavailable, PayoutError


class Transport:
    """Sends one message and returns the decoded reply body."""

    def send(self, message):
        raise NotImplementedError


class HttpTransport(Transport):
    """Posts messages with an injected HTTP session.

    ``session.post(url, json=..., timeout=...)`` returns ``(status, body)`` and
    raises TimeoutError when no reply arrives in time.
    """

    def __init__(self, session, base_url, timeout=10.0):
        self._session = session
        self._url = base_url.rstrip("/") + "/v2/messages"
        self._timeout = timeout

    def send(self, message):
        try:
            status, body = self._session.post(self._url, json=message, timeout=self._timeout)
        except TimeoutError:
            raise GatewayTimeout(f"no reply within {self._timeout:.1f}s") from None
        return raise_for_status(status, body)


def raise_for_status(status, body):
    """Return ``body`` for a 2xx status, otherwise raise the matching error."""
    if 200 <= status < 300:
        return body
    if status in (502, 503):
        raise GatewayUnavailable(f"gateway answered {status}")
    if status == 504:
        raise GatewayTimeout("gateway timed out upstream")
    raise PayoutError(f"gateway answered {status}")
