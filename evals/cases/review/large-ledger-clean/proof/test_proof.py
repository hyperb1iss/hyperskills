import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from ledger.accounts import create_account
from ledger.closing import close_period
from ledger.db import Store
from ledger.fx import MissingRate, RateTable, record_rate
from ledger.importer import import_statement
from ledger.journal import Entry, Line, post
from ledger.migrations import migrate
from ledger.periods import closed_through
from tests.support import make_store


class RateEffectiveDateProof(unittest.TestCase):
    def test_a_rate_applies_from_its_own_date(self):
        rates = RateTable()
        rates.add("EUR", date(2026, 1, 1), Decimal("1.0800"))
        rates.add("EUR", date(2026, 2, 1), Decimal("1.1000"))
        self.assertEqual(rates.find("EUR", date(2026, 2, 1)), Decimal("1.1000"))
        self.assertEqual(rates.find("EUR", date(2026, 1, 1)), Decimal("1.0800"))


class RevaluationCoverageProof(unittest.TestCase):
    def test_close_refuses_a_foreign_balance_without_a_closing_rate(self):
        store = make_store()
        create_account(store, "1010", "Euro bank", "asset", "EUR")
        record_rate(store, "EUR", date(2026, 1, 2), Decimal("1.0800"))
        post(store, Entry(date(2026, 1, 10), "Fund", [Line("1010", debit=1000000), Line("3000", credit=1080000)]))
        record_rate(store, "EUR", date(2026, 1, 20), Decimal("1.1500"))
        with self.assertRaises(MissingRate):
            close_period(store, date(2026, 1, 31))
        self.assertIsNone(closed_through(store))


class ImportKeyMigrationProof(unittest.TestCase):
    def test_reimporting_after_the_migration_posts_nothing(self):
        store = Store()
        migrate(store, target=2)
        for code, name in (("1000", "Operating bank"), ("1100", "Bank clearing")):
            store.insert("accounts", {"code": code, "name": name, "kind": "asset"})
        entry = store.insert("entries", {"posted_on": "2026-01-04", "memo": "Customer payment",
                                         "source": "operating", "external_id": "TX-1"})
        store.insert("lines", {"entry_id": entry["id"], "account": "1000", "debit": 120000, "credit": 0, "memo": ""})
        store.insert("lines", {"entry_id": entry["id"], "account": "1100", "debit": 0, "credit": 120000, "memo": ""})
        store.insert("import_keys", {"key": "TX-1"})
        migrate(store)
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "statement.csv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("date,reference,description,amount\n2026-01-04,TX-1,Customer payment,1200.00\n")
            result = import_statement(store, path, "operating", "1000", "1100")
        self.assertEqual(result.posted, [])
        self.assertEqual(result.skipped, ["TX-1"])


if __name__ == "__main__":
    unittest.main()
