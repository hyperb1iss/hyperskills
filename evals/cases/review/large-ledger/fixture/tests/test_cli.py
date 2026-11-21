import io
import os
import tempfile
import unittest

from ledger.cli import main
from ledger.db import Store

from .support import make_store


class CliTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.books = os.path.join(temp.name, "books.json")
        self.statement = os.path.join(temp.name, "statement.csv")
        make_store().save(self.books)
        with open(self.statement, "w", encoding="utf-8") as handle:
            handle.write("date,reference,description,amount\n2026-01-04,TX-1,Payment,10.00\n2026-01-05,,x,1\n")

    def run_cli(self, *args):
        out = io.StringIO()
        return main([self.books, *args], out=out), out.getvalue()

    def test_import_reports_and_saves(self):
        status, text = self.run_cli("import", self.statement, "--source", "operating", "--bank", "1000",
                                    "--clearing", "1100")
        self.assertEqual(status, 1)
        self.assertTrue(text.startswith("posted 1, skipped 0, rejected 1"))
        self.assertEqual(len(Store.load(self.books).table("entries")), 1)

    def test_old_books_must_be_migrated_first(self):
        Store(schema_version=1).save(self.books)
        with self.assertRaises(SystemExit):
            self.run_cli("trial-balance")
        self.assertEqual(self.run_cli("migrate")[1].strip()[:18], "applied migrations")

    def test_close(self):
        self.assertEqual(self.run_cli("close", "2026-01-31"), (0, "closed through 2026-01-31\n"))


if __name__ == "__main__":
    unittest.main()
