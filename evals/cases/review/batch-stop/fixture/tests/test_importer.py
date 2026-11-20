import os
import tempfile
import unittest
from io import StringIO

from gridmeter import cli
from gridmeter.importer import import_file
from gridmeter.store import ReadingStore

HEADER = "meter,timestamp,value,unit\n"


class ImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = temp.name

    def write(self, body, encoding="utf-8"):
        path = os.path.join(self.dir, "drop.csv")
        with open(path, "w", encoding=encoding) as handle:
            handle.write(HEADER + body)
        return path

    def test_imports_every_row_in_one_write(self):
        path = self.write("m-1,2026-03-01 10:00,1.5,kWh\nm-2,2026-03-01T11:00:00+01:00,900,Wh\n")
        store = ReadingStore()
        summary = import_file(path, store)
        self.assertEqual((summary.imported, summary.rejected), (2, []))
        self.assertEqual((store.count(), store.writes), (2, 1))

    def test_reimport_counts_only_new_readings(self):
        path = self.write("m-1,2026-03-01 10:00,1.5,kWh\n", encoding="utf-8-sig")
        store = ReadingStore()
        self.assertEqual(import_file(path, store).imported, 1)
        self.assertEqual(import_file(path, store).imported, 0)

    def test_rejected_row_is_reported(self):
        path = self.write("m-1,2026-03-01 10:00,1.5,kWh\n\nm-2,2026-03-01 10:00,900,Wh\nm-3,2026-03-01 10:00,n/a,kWh\n")
        summary = import_file(path, ReadingStore())
        self.assertEqual(summary.imported, 2)
        self.assertEqual(summary.rejected, ["line 5: meter m-3: not a number: 'n/a'"])

    def test_cli_exit_code_reflects_rejections(self):
        path = self.write("m-1,2026-03-01 10:00,1.5,kWh\nm-2,,1,kWh\n")
        out = StringIO()
        self.assertEqual(cli.main(["import", path], out=out), 1)
        self.assertEqual(out.getvalue(), f"{path}: imported 1, rejected 1\n  line 3: meter m-2: bad timestamp\n")


if __name__ == "__main__":
    unittest.main()
