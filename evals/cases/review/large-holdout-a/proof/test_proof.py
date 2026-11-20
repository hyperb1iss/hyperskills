import unittest
from datetime import datetime, timedelta, timezone

from stockpile import inventory, reservations
from stockpile.access import OPERATOR, Forbidden, authorize, issue_key
from stockpile.models import Bin
from stockpile.notify import MemoryTransport, Notifier
from stockpile.store import Store
from stockpile.worker import ExpiryWorker

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


class ScopeProof(unittest.TestCase):
    def test_a_key_with_an_empty_scope_acts_in_no_warehouse(self):
        store = Store()
        key, _ = issue_key(store, OPERATOR)
        with self.assertRaises(Forbidden):
            authorize(key, "reserve", "WH-1")


class WorkerMemoryProof(unittest.TestCase):
    def test_worker_forgets_holds_that_were_confirmed_or_cancelled(self):
        store = Store()
        store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 500))
        holds = [reservations.reserve(store, "key-1", f"order-{n}", "TEA-0001", "A-01", 1, NOW,
                                      timedelta(minutes=4))
                 for n in range(200)]
        worker = ExpiryWorker(store, Notifier(MemoryTransport()), lambda: NOW)
        self.assertEqual(worker.tick()["warned"], 200)
        for n, hold in enumerate(holds):
            if n % 2:
                reservations.confirm(store, hold.reservation_id, NOW)
            else:
                reservations.cancel(store, hold.reservation_id)
        worker.tick()
        self.assertEqual(len(worker._warned), 0)


class ExpiredStockProof(unittest.TestCase):
    def test_an_expired_hold_leaves_its_units_free(self):
        store = Store()
        store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 10))
        hold = reservations.reserve(store, "key-1", "order-1", "TEA-0001", "A-01", 10, NOW,
                                    timedelta(minutes=10))
        later = NOW + timedelta(minutes=10)
        self.assertEqual(inventory.free_in_bin(store, "A-01", later), 10)
        self.assertTrue(reservations.expire_hold(store, hold.reservation_id, later))
        self.assertEqual(inventory.free_in_bin(store, "A-01", later), 10)


if __name__ == "__main__":
    unittest.main()
