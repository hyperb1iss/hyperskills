import unittest
from datetime import datetime, timedelta, timezone

from courier.outbox import Outbox

NOON = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)


class OutboxTests(unittest.TestCase):
    def test_pending_is_ordered_and_limited(self):
        outbox = Outbox()
        for n in range(4):
            outbox.add("orders.created", {"n": n})
        self.assertEqual([row.id for row in outbox.pending(3)], [1, 2, 3])

    def test_published_rows_leave_pending(self):
        outbox = Outbox()
        first = outbox.add("orders.created", {})
        outbox.add("orders.created", {})
        outbox.mark_published([first.id], NOON)
        self.assertEqual([row.id for row in outbox.pending(10)], [2])

    def test_purge_keeps_pending_and_recent_rows(self):
        outbox = Outbox()
        old, recent, waiting = (outbox.add("orders.created", {}) for _ in range(3))
        outbox.mark_published([old.id], NOON - timedelta(days=8))
        outbox.mark_published([recent.id], NOON)
        self.assertEqual(outbox.purge_published(NOON - timedelta(days=7)), 1)
        self.assertEqual([row.id for row in outbox.pending(10)], [waiting.id])
        self.assertEqual(outbox.get(recent.id).published_at, NOON)


if __name__ == "__main__":
    unittest.main()
