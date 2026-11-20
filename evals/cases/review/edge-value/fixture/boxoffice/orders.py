"""Reserving and cancelling tickets."""
from . import notify
from .models import ACTIVE, CANCELLED, Reservation

MAX_TICKETS_PER_BUYER = 4


class LimitReached(Exception):
    pass


def reserve(store, event_id, buyer):
    event = store.event(event_id)
    held = [t for t in store.tickets_held_by(buyer) if t.event_id == event_id]
    if len(held) >= MAX_TICKETS_PER_BUYER:
        raise LimitReached(f"{buyer} already holds {len(held)} tickets for {event_id}")
    sold = store.count_active(event_id)
    if sold > event.capacity:
        position = store.waitlist(event_id).join(buyer)
        notify.waitlist_joined(store.outbox, event, buyer, position)
        return Reservation(event_id, buyer, waitlist_position=position)
    ticket = store.issue_ticket(event_id, buyer)
    notify.ticket_confirmed(store.outbox, event, ticket)
    return Reservation(event_id, buyer, ticket=ticket)


def cancel(store, ticket_id):
    ticket = store.ticket(ticket_id)
    if ticket.status != ACTIVE:
        return None
    ticket.status = CANCELLED
    event = store.event(ticket.event_id)
    notify.ticket_cancelled(store.outbox, event, ticket)
    queue = store.waitlist(event.id)
    if queue and store.count_active(event.id) < event.capacity:
        promoted = store.issue_ticket(event.id, queue.pop_next())
        notify.ticket_confirmed(store.outbox, event, promoted)
        return promoted
    return None
