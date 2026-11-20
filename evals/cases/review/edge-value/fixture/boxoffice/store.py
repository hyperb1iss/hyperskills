from itertools import count

from .models import ACTIVE, Event, Ticket
from .waitlist import Waitlist


class UnknownEvent(KeyError):
    pass


class Store:
    """In-memory storage shared by the API process and the tests."""

    def __init__(self):
        self.events = {}
        self.tickets = {}
        self.waitlists = {}
        self.outbox = []
        self._ids = count(1)

    def add_event(self, event: Event):
        self.events[event.id] = event
        return event

    def event(self, event_id):
        try:
            return self.events[event_id]
        except KeyError:
            raise UnknownEvent(event_id) from None

    def ticket(self, ticket_id):
        return self.tickets[ticket_id]

    def issue_ticket(self, event_id, buyer):
        ticket = Ticket(id=next(self._ids), event_id=event_id, buyer=buyer)
        self.tickets[ticket.id] = ticket
        return ticket

    def tickets_for(self, event_id):
        return [t for t in self.tickets.values() if t.event_id == event_id]

    def tickets_held_by(self, buyer):
        return [t for t in self.tickets.values() if t.buyer == buyer and t.status == ACTIVE]

    def count_active(self, event_id):
        return sum(1 for t in self.tickets_for(event_id) if t.status == ACTIVE)

    def waitlist(self, event_id):
        self.event(event_id)
        return self.waitlists.setdefault(event_id, Waitlist())
