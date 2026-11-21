import unittest
from datetime import datetime

from boxoffice import orders
from boxoffice.models import Event
from boxoffice.store import Store


class CapacityProof(unittest.TestCase):
    def test_event_never_sells_more_tickets_than_seats(self):
        store = Store()
        store.add_event(Event("gala", "Spring Gala", 2, datetime(2026, 5, 2, 19, 0)))
        results = [orders.reserve(store, "gala", f"fan{n}@example.com") for n in range(3)]
        self.assertEqual([r.confirmed for r in results], [True, True, False])
        self.assertEqual(store.count_active("gala"), 2)
        self.assertEqual(results[2].waitlist_position, 1)


if __name__ == "__main__":
    unittest.main()
