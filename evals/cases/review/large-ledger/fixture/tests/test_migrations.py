import os
import tempfile
import unittest

from ledger.db import Store
from ledger.migrations import available, migrate


class MigrationTests(unittest.TestCase):
    def test_numbers_are_contiguous(self):
        numbers = [number for number, _ in available()]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_migrate_runs_each_migration_once(self):
        store = Store()
        self.assertEqual(migrate(store), [number for number, _ in available()])
        self.assertEqual(migrate(store), [])

    def test_import_keys_backfill_from_entries(self):
        store = Store()
        migrate(store, target=1)
        store.insert("entries", {"posted_on": "2026-01-04", "memo": "x", "external_id": "TX-9"})
        store.insert("entries", {"posted_on": "2026-01-05", "memo": "manual"})
        migrate(store, target=2)
        self.assertEqual([row["key"] for row in store.table("import_keys")], ["TX-9"])
        self.assertIsNone(store.select("entries", memo="manual")[0]["source"])

    def test_multi_currency_backfill(self):
        store = Store()
        migrate(store, target=2)
        store.insert("accounts", {"code": "1000", "name": "Bank", "kind": "asset"})
        entry = store.insert("entries", {"posted_on": "2026-01-04", "memo": "x", "source": "operating",
                                         "external_id": "TX-9"})
        store.insert("lines", {"entry_id": entry["id"], "account": "1000", "debit": 500, "credit": 0, "memo": ""})
        store.insert("import_keys", {"key": "TX-9"})
        migrate(store)
        self.assertEqual(store.one("accounts", code="1000")["currency"], "USD")
        line = store.table("lines")[0]
        self.assertEqual((line["currency"], line["base_debit"], line["base_credit"]), ("USD", 500, 0))
        self.assertEqual(len(store.table("import_keys")), 1)
        self.assertTrue({"7910", "7920", "7990"} <= {row["code"] for row in store.table("accounts")})

    def test_round_trip_through_a_file(self):
        store = Store()
        migrate(store)
        store.insert("accounts", {"code": "1000", "name": "Bank", "kind": "asset"})
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "books.json")
            store.save(path)
            loaded = Store.load(path)
        self.assertEqual(loaded.schema_version, store.schema_version)
        self.assertEqual(loaded.tables["accounts"], store.tables["accounts"])


if __name__ == "__main__":
    unittest.main()
