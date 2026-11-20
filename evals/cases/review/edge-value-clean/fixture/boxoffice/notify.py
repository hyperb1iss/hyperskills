"""Customer email. The mailer worker drains store.outbox."""


def _message(to, subject, body):
    return {"to": to, "subject": subject, "body": body}


def ticket_confirmed(outbox, event, ticket):
    outbox.append(_message(
        ticket.buyer,
        f"Your ticket for {event.name}",
        f"Ticket #{ticket.id} for {event.name} on {event.starts_at:%b %d} is confirmed.",
    ))


def ticket_cancelled(outbox, event, ticket):
    outbox.append(_message(
        ticket.buyer,
        f"Cancelled: {event.name}",
        f"Ticket #{ticket.id} for {event.name} has been cancelled and refunded.",
    ))


def waitlist_joined(outbox, event, buyer, position):
    ahead = "1 person" if position == 2 else f"{position - 1} people"
    body = f"{event.name} is sold out. You are number {position} on the waitlist with {ahead} ahead of you."
    outbox.append(_message(buyer, f"Waitlist: {event.name}", body))
