import hashlib
import unittest
from datetime import datetime, timedelta, timezone

from stockpile import inventory
from stockpile.access import authenticate
from stockpile.migrations import migrate
from stockpile.store import Store

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)


def v3_store():
    bin_ = {"bin_id": "A-01", "warehouse_id": "WH-1", "sku": "TEA-0001", "quantity": 10, "lot_expires": None}
    rows = {rid: {"reservation_id": rid, "key_id": "key-op", "order_ref": f"order-{rid}", "sku": "TEA-0001",
                  "bin_id": "A-01", "quantity": rid + 2, "status": status,
                  "created_at": "2026-10-30T15:00:00+00:00"}
            for rid, status in ((1, "held"), (2, "confirmed"))}
    keys = {key_id: {"key_id": key_id, "role": role, "revoked": False,
                     "digest": hashlib.sha256(f"secret-{key_id}".encode()).hexdigest()}
            for key_id, role in (("key-op", "operator"), ("key-admin", "admin"))}
    return Store.load({"bins": {"A-01": bin_}, "reservations": rows, "keys": keys}, schema_version=3)


class HoldsAndScopesMigrationTest(unittest.TestCase):
    def test_existing_holds_never_lapse(self):
        store = v3_store()
        self.assertEqual(migrate(store, NOW), [4])
        self.assertIsNone(store.reservation(1).expires_at)
        self.assertEqual(store.holds_expiring_before(NOW + timedelta(days=365)), [])
        self.assertEqual(inventory.free_in_bin(store, "A-01", NOW + timedelta(days=365)), 3)
        self.assertEqual((store.schema_version, store.next_id("reservations")), (4, 3))
        self.assertEqual(migrate(store, NOW), [])

    def test_existing_keys_keep_every_warehouse(self):
        store = v3_store()
        migrate(store, NOW)
        for key_id in ("key-op", "key-admin"):
            key = authenticate(store, f"Bearer {key_id}.secret-{key_id}")
            self.assertEqual(key.warehouses, ("*",))


if __name__ == "__main__":
    unittest.main()
