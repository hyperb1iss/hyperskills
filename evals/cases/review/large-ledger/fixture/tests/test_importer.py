import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from ledger.accounts import create_account
from ledger.balances import balance, foreign_balance
from ledger.fx import record_rate
from ledger.importer import import_statement

from .support import make_store

HEADER = "date,reference,description,amount\n"


class ImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = temp.name
        self.store = make_store()

    def write(self, body, name="statement.csv"):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(HEADER + body)
        return path

    def run_import(self, path, source="operating"):
        return import_statement(self.store, path, source, "1000", "1100")

    def test_money_in_and_out(self):
        path = self.write("2026-01-04,TX-1,Customer payment,1200.00\n2026-01-05,TX-2,Card fees,-35.10\n")
        result = self.run_import(path)
        self.assertEqual(len(result.posted), 2)
        self.assertEqual(balance(self.store, "1000"), 120000 - 3510)
        self.assertEqual(balance(self.store, "1100"), -120000 + 3510)

    def test_reimport_skips_known_references(self):
        path = self.write("2026-01-04,TX-1,Customer payment,1200.00\n")
        self.run_import(path)
        result = self.run_import(path)
        self.assertEqual((result.posted, result.skipped), ([], ["TX-1"]))

    def test_bad_rows_are_reported_and_the_rest_imported(self):
        path = self.write("2026-01-04,TX-1,ok,10.00\n2026-13-01,TX-2,bad date,5.00\n,TX-3,no date,1.00\n"
                          "2026-01-06,,no reference,2.00\n2026-01-07,TX-5,zero,0\n2026-01-08,TX-6,ok,3.00\n")
        result = self.run_import(path)
        self.assertEqual(len(result.posted), 2)
        self.assertEqual([r.split(":")[0] for r in result.rejected], ["line 3", "line 4", "line 5", "line 6"])

    def test_closed_period_rows_are_rejected(self):
        self.store.insert("periods", {"end": date(2026, 1, 31).isoformat()})
        result = self.run_import(self.write("2026-01-30,TX-1,late,10.00\n2026-02-02,TX-2,ok,10.00\n"))
        self.assertEqual(len(result.posted), 1)
        self.assertIn("closed period", result.rejected[0])


class EuroFeedTests(ImportTests):
    def setUp(self):
        super().setUp()
        create_account(self.store, "1010", "Euro bank", "asset", "EUR")
        create_account(self.store, "1110", "Euro clearing", "asset", "EUR")
        record_rate(self.store, "EUR", date(2026, 1, 1), Decimal("1.0850"))

    def test_amounts_are_in_the_bank_currency(self):
        path = self.write("2026-01-04,TX-1,Euro customer,250.50\n")
        import_statement(self.store, path, "operating-eur", "1010", "1110")
        self.assertEqual(foreign_balance(self.store, "1010"), 25050)

    def test_references_are_scoped_to_the_feed(self):
        path = self.write("2026-01-04,TX-1,Payment,10.00\n")
        self.assertEqual(len(self.run_import(path).posted), 1)
        self.assertEqual(len(import_statement(self.store, path, "operating-eur", "1010", "1110").posted), 1)
        self.assertEqual(self.run_import(path).skipped, ["TX-1"])

    def test_missing_rate_rejects_the_row_only(self):
        path = self.write("2025-12-30,TX-1,Too early,10.00\n2026-01-05,TX-2,ok,10.00\n")
        result = import_statement(self.store, path, "operating-eur", "1010", "1110")
        self.assertEqual(len(result.posted), 1)
        self.assertIn("no EUR rate", result.rejected[0])

if __name__ == "__main__":
    unittest.main()
