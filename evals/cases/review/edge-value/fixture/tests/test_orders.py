import unittest
from datetime import datetime

from boxoffice import orders
from boxoffice.models import CANCELLED, Event
from boxoffice.store import Store


def make_store(capacity=3):
    store = Store()
    store.add_event(Event("gala", "Spring Gala", capacity, datetime(2026, 5, 2, 19, 0)))
    return store


class ReserveTests(unittest.TestCase):
    def test_reserve_issues_ticket_and_confirms(self):
        store = make_store()
        ticket = orders.reserve(store, "gala", "ana@example.com").ticket
        self.assertEqual(ticket.buyer, "ana@example.com")
        self.assertEqual(store.outbox[-1]["subject"], "Your ticket for Spring Gala")

    def test_buyer_limit(self):
        store = make_store(capacity=10)
        for _ in range(orders.MAX_TICKETS_PER_BUYER):
            orders.reserve(store, "gala", "ben@example.com")
        with self.assertRaises(orders.LimitReached):
            orders.reserve(store, "gala", "ben@example.com")

    def test_sold_out_event_offers_waitlist(self):
        store = make_store(capacity=2)
        results = [orders.reserve(store, "gala", f"fan{n}@example.com") for n in range(5)]
        waiting = [r.waitlist_position for r in results if not r.confirmed]
        self.assertEqual(waiting, list(range(1, len(waiting) + 1)))
        self.assertEqual(store.outbox[-1]["subject"], "Waitlist: Spring Gala")

    def test_cancel_frees_seat(self):
        store = make_store(capacity=1)
        ticket = orders.reserve(store, "gala", "ana@example.com").ticket
        orders.cancel(store, ticket.id)
        self.assertEqual(store.ticket(ticket.id).status, CANCELLED)
        self.assertTrue(orders.reserve(store, "gala", "ben@example.com").confirmed)

    def test_cancel_promotes_first_waiting_buyer(self):
        store = make_store(capacity=1)
        ticket = orders.reserve(store, "gala", "ana@example.com").ticket
        store.waitlist("gala").join("ben@example.com")
        promoted = orders.cancel(store, ticket.id)
        self.assertEqual(promoted.buyer, "ben@example.com")
        self.assertEqual(store.outbox[-1]["to"], "ben@example.com")


if __name__ == "__main__":
    unittest.main()
