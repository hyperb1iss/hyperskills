"""Outgoing mail: addresses, messages, and transports."""

import re
from dataclasses import dataclass

ADDRESS = re.compile(r"[^@\s,;<>]+@[^@\s,;<>]+\.[A-Za-z]{2,}")


class InvalidAddress(ValueError):
    """The address cannot be delivered to as written."""


class TransportError(Exception):
    """The relay did not take the message. Sending it again later may work."""


def parse_address(raw):
    """Return the deliverable form of ``raw``, or raise InvalidAddress."""
    address = (raw or "").strip()
    if not ADDRESS.fullmatch(address):
        raise InvalidAddress(raw)
    return address


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str
    sender: str
    category: str


class Transport:
    """Delivers one message. ``message.to`` must come from parse_address."""

    def send(self, message):
        raise NotImplementedError


class RecordingTransport(Transport):
    """Keeps messages in memory instead of sending them.

    Tests use it, and so does every command's dry-run mode. Addresses listed in
    ``refuse`` raise TransportError, as the relay does when it rejects a message.
    """

    def __init__(self, refuse=()):
        self.sent = []
        self._refuse = set(refuse)

    def send(self, message):
        if message.to in self._refuse:
            raise TransportError(f"relay refused {message.to}")
        self.sent.append(message)


class RelayTransport(Transport):
    """Submits messages to the outbound relay through an injected client.

    ``client.submit(envelope)`` raises ConnectionError or TimeoutError when the relay
    cannot be reached, and another exception when the relay refuses the envelope.
    Every one of those failures is raised as TransportError.
    """

    def __init__(self, client, max_body_bytes=256_000):
        self._client = client
        self._max_body_bytes = max_body_bytes

    def send(self, message):
        if len(message.body.encode("utf-8")) > self._max_body_bytes:
            raise TransportError("message body is larger than the relay accepts")
        envelope = {
            "to": message.to,
            "from": message.sender,
            "subject": message.subject,
            "body": message.body,
            "category": message.category,
        }
        try:
            self._client.submit(envelope)
        except Exception as exc:
            raise TransportError(str(exc)) from exc
