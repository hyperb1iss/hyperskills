"""Outbound notices to API clients.

A Notifier hands each notice to a transport callable; in production that is
the client callback sender. Delivery is best effort: when the transport fails,
send raises NotifyError and the caller decides whether to try again later.
"""
from dataclasses import dataclass


class NotifyError(Exception):
    pass


@dataclass(frozen=True)
class Notice:
    recipient: str
    kind: str
    payload: dict


class Notifier:
    def __init__(self, transport):
        self.transport = transport

    def send(self, recipient, kind, payload):
        notice = Notice(recipient, kind, dict(payload))
        try:
            self.transport(notice)
        except Exception as error:
            raise NotifyError(f"could not deliver {kind} to {recipient}: {error}") from error
        return notice


class MemoryTransport:
    """A transport that keeps notices in a list, for tests and local runs."""

    def __init__(self):
        self.sent = []

    def __call__(self, notice):
        self.sent.append(notice)
