"""Immediate notifications: one email per event, sent shortly after it arrives."""

import logging
from dataclasses import dataclass

from .mailer import InvalidAddress, Message, TransportError, parse_address

log = logging.getLogger(__name__)


@dataclass
class NotifyReport:
    sent: int = 0
    skipped: int = 0


def event_message(user, address, event, sender):
    lines = [f"Hi {user.name or 'there'},", "", event.subject]
    if event.url:
        lines += ["", event.url]
    return Message(
        to=address,
        subject=event.subject,
        body="\n".join(lines) + "\n",
        sender=sender,
        category="immediate",
    )


def notify_new_events(store, users, prefs, transport, since, until, sender):
    """Email each event received in (since, until] to users who want it right away.

    An address that cannot be parsed skips that user's events, and a relay failure
    skips that one message; neither stops the run.
    """
    report = NotifyReport()
    for user in users.active():
        user_prefs = prefs.get(user.id)
        events = [
            event for event in store.received_between(user.id, since, until)
            if user_prefs.wants_immediate(event.kind)
        ]
        if not events:
            continue
        try:
            address = parse_address(user.email)
        except InvalidAddress:
            log.warning("user %s has an unusable address; skipping %d events", user.id, len(events))
            report.skipped += len(events)
            continue
        for event in events:
            try:
                transport.send(event_message(user, address, event, sender))
            except TransportError as exc:
                log.warning("event %s for user %s not sent: %s", event.id, user.id, exc)
                report.skipped += 1
                continue
            report.sent += 1
    return report
