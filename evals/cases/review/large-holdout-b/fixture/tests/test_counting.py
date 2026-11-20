import unittest
from datetime import date

from stockroom.counting import count_sheet, reconcile
from stockroom.snapshots import nightly_export

from tests.helpers import make_stock


class CountingTests(unittest.TestCase):
    def test_count_sheet_lists_expected_units(self):
        stock, _ = make_stock()
        self.assertEqual(count_sheet(stock, "east"), [("MUG-02", 3), ("TEA-01", 16)])

    def test_reconcile_posts_differences_to_home_bin(self):
        stock, _ = make_stock()
        posted = reconcile(stock, "east", {"TEA-01": 14, "MUG-02": 3})
        self.assertEqual(posted, {"TEA-01": -2})
        self.assertEqual(stock.bin("east", "E-01").on_hand, 8)

    def test_reconcile_rejects_negative_counts(self):
        stock, _ = make_stock()
        with self.assertRaises(ValueError):
            reconcile(stock, "east", {"TEA-01": -1})

    def test_nightly_export_rows(self):
        stock, _ = make_stock()
        rows = nightly_export(stock, date(2026, 4, 6))
        self.assertIn(("2026-04-06", "west", "TEA-01", 8), rows)
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
