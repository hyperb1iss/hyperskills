import unittest
from datetime import date

from stockroom.models import Bin
from stockroom.stock import InsufficientStock, UnknownBin

from tests.helpers import make_stock


class LevelTests(unittest.TestCase):
    def test_available_sums_bins_in_a_warehouse(self):
        stock, _ = make_stock()
        self.assertEqual(stock.available("TEA-01", "east"), 16)
        self.assertEqual(stock.available("TEA-01"), 24)

    def test_duplicate_bin_rejected(self):
        stock, _ = make_stock()
        with self.assertRaises(ValueError):
            stock.add_bin(Bin("east", "E-01", "TEA-01"))

    def test_skus_and_warehouses(self):
        stock, _ = make_stock()
        self.assertEqual(stock.warehouse_ids(), ["east", "west"])
        self.assertEqual(stock.skus("west"), ["TEA-01"])


class AdjustAndReceiveTests(unittest.TestCase):
    def test_adjust_defaults_to_home_bin(self):
        stock, _ = make_stock()
        target = stock.adjust("TEA-01", "east", None, -2, "damaged")
        self.assertEqual((target.bin_id, target.on_hand), ("E-01", 8))

    def test_adjust_cannot_go_negative(self):
        stock, _ = make_stock()
        with self.assertRaises(InsufficientStock):
            stock.adjust("MUG-02", "east", "E-04", -4, "count")

    def test_adjust_unknown_bin(self):
        stock, _ = make_stock()
        with self.assertRaises(UnknownBin):
            stock.adjust("TEA-01", "east", "E-77", 1, "count")

    def test_receive_into_empty_bin_restamps_date(self):
        stock, _ = make_stock()
        stock.pick("MUG-02", "east", 3)
        target = stock.receive("MUG-02", "east", 12, date(2026, 4, 2))
        self.assertEqual((target.on_hand, target.received_on), (12, date(2026, 4, 2)))


class PickTests(unittest.TestCase):
    def test_pick_spans_bins(self):
        stock, _ = make_stock()
        takes = stock.pick("TEA-01", "east", 12)
        self.assertEqual(takes, [("E-01", 10), ("E-09", 2)])
        self.assertEqual(stock.on_hand("TEA-01", "east"), 4)

    def test_pick_short_takes_nothing(self):
        stock, _ = make_stock()
        with self.assertRaises(InsufficientStock) as caught:
            stock.pick("TEA-01", "west", 9)
        self.assertEqual(caught.exception.available, 8)
        self.assertEqual(stock.on_hand("TEA-01", "west"), 8)

    def test_same_day_bins_are_picked_in_walk_order(self):
        stock, _ = make_stock()
        stock.add_bin(Bin("west", "W-12", "SOAP-3", on_hand=4, pick_order=12, received_on=date(2026, 3, 9)))
        stock.add_bin(Bin("west", "W-02", "SOAP-3", on_hand=4, pick_order=2, received_on=date(2026, 3, 9)))
        self.assertEqual(stock.pick("SOAP-3", "west", 5), [("W-02", 4), ("W-12", 1)])

    def test_pick_leaves_reserved_units(self):
        stock, _ = make_stock()
        stock.hold("west", "W-03", 6)
        with self.assertRaises(InsufficientStock):
            stock.pick("TEA-01", "west", 3)
        self.assertEqual(stock.pick("TEA-01", "west", 2), [("W-03", 2)])


class HoldTests(unittest.TestCase):
    def test_take_held_yields_what_the_bin_has(self):
        stock, _ = make_stock()
        stock.hold("east", "E-04", 3)
        stock.adjust("MUG-02", "east", "E-04", -2, "damaged")
        self.assertEqual(stock.take_held("east", "E-04", 3), 1)
        self.assertEqual((stock.on_hand("MUG-02"), stock.reserved("MUG-02")), (0, 0))


if __name__ == "__main__":
    unittest.main()
