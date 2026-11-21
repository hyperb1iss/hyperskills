import unittest

from stockroom.reports import low_stock, stock_report

from tests.helpers import make_stock


class StockReportTests(unittest.TestCase):
    def test_rows_per_sku_and_warehouse(self):
        stock, _ = make_stock()
        rows = stock_report(stock, ["east"])
        self.assertEqual([(r["sku"], r["units"]) for r in rows], [("MUG-02", 3), ("TEA-01", 16)])

    def test_rows_split_reserved_units(self):
        stock, _ = make_stock()
        stock.hold("east", "E-01", 7)
        row = [r for r in stock_report(stock, ["east"]) if r["sku"] == "TEA-01"][0]
        self.assertEqual((row["units"], row["reserved"], row["available"]), (16, 7, 9))

    def test_low_stock_uses_units_free_to_promise(self):
        stock, _ = make_stock()
        stock.hold("west", "W-03", 4)
        self.assertEqual([(r["warehouse"], r["sku"]) for r in low_stock(stock, ["east", "west"], 4)],
                         [("east", "MUG-02"), ("west", "TEA-01")])


if __name__ == "__main__":
    unittest.main()
