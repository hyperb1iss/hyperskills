import unittest
from datetime import date

from stockpile import reports
from stockpile.catalog import Catalog, Product
from stockpile.models import Bin
from stockpile.notify import MemoryTransport, Notifier
from stockpile.store import Store


class ReportsTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 10, date(2026, 12, 1)))
        self.store.add_bin(Bin("A-02", "WH-1", "TEA-0001", 5, date(2026, 11, 20)))
        self.store.add_bin(Bin("C-01", "WH-1", "CUP-0002", 2))
        self.catalog = Catalog([Product("TEA-0001", "Loose leaf")])

    def test_stock_report_groups_bins_by_sku(self):
        lines = reports.stock_report(self.store, self.catalog, "WH-1")
        self.assertEqual([line["sku"] for line in lines], ["CUP-0002", "TEA-0001"])
        self.assertEqual(lines[1]["on_hand"], 15)
        self.assertEqual(lines[1]["bins"], 2)
        self.assertEqual(lines[1]["description"], "Loose leaf")
        self.assertEqual(lines[0]["description"], "CUP-0002")

    def test_expiring_lots_are_soonest_first(self):
        found = reports.expiring_lots(self.store, "WH-1", date(2026, 11, 18), within_days=14)
        self.assertEqual([bin_.bin_id for bin_ in found], ["A-02", "A-01"])
        found = reports.expiring_lots(self.store, "WH-1", date(2026, 11, 18), within_days=5)
        self.assertEqual([bin_.bin_id for bin_ in found], ["A-02"])

    def test_low_stock_alerts_go_to_the_recipient(self):
        transport = MemoryTransport()
        alerted = reports.send_low_stock_alerts(self.store, Notifier(transport), "ops", "WH-1", 3)
        self.assertEqual(alerted, ["CUP-0002"])
        self.assertEqual(transport.sent[0].payload["available"], 2)


if __name__ == "__main__":
    unittest.main()
