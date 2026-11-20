import unittest
from datetime import datetime, timedelta, timezone

from stockpile import reservations
from stockpile.models import CONFIRMED, EXPIRED, Bin
from stockpile.notify import MemoryTransport, Notifier
from stockpile.store import Store
from stockpile.worker import ExpiryWorker

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


class ExpiryWorkerTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 20))
        self.now = NOW
        self.transport = MemoryTransport()
        self.worker = ExpiryWorker(self.store, Notifier(self.transport), lambda: self.now)

    def hold(self, minutes, key_id="key-1"):
        return reservations.reserve(self.store, key_id, "order-1", "TEA-0001", "A-01", 1, NOW,
                                    timedelta(minutes=minutes) if minutes else None)

    def test_each_lapsing_hold_is_warned_once(self):
        soon = self.hold(4, key_id="key-7")
        self.hold(20)
        self.hold(None)
        self.assertEqual(self.worker.tick(), {"expired": 0, "warned": 1, "failed": 0})
        self.assertEqual(self.worker.tick(), {"expired": 0, "warned": 0, "failed": 0})
        [notice] = self.transport.sent
        self.assertEqual((notice.recipient, notice.kind), ("key-7", "hold_expiring"))
        self.assertEqual(notice.payload["reservation_id"], soon.reservation_id)

    def test_lapsed_holds_are_expired_and_confirmed_ones_are_not(self):
        lapsed = self.hold(10)
        kept = self.hold(10)
        reservations.confirm(self.store, kept.reservation_id, NOW)
        self.now = NOW + timedelta(minutes=10)
        self.assertEqual(self.worker.tick()["expired"], 1)
        self.assertEqual(self.store.reservation(lapsed.reservation_id).status, EXPIRED)
        self.assertEqual(self.store.reservation(kept.reservation_id).status, CONFIRMED)


if __name__ == "__main__":
    unittest.main()
