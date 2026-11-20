import os
import tempfile
import unittest

from gridmeter.importer import import_file
from gridmeter.store import ReadingStore


class RowIsolationProof(unittest.TestCase):
    def test_rows_after_a_rejected_row_are_still_imported(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "drop.csv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("meter,timestamp,value,unit\n"
                             "m-1,2026-03-01 10:00,1.5,kWh\n"
                             "m-2,2026-03-01 10:00,n/a,kWh\n"
                             "m-3,2026-03-01 10:00,2.5,kWh\n")
            store = ReadingStore()
            summary = import_file(path, store)
        self.assertEqual(len(summary.rejected), 1)
        self.assertEqual(summary.imported, 2)
        self.assertEqual([r.meter_id for r in store.for_meter("m-3")], ["m-3"])


if __name__ == "__main__":
    unittest.main()
