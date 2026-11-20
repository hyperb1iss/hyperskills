import unittest

from stockpile import inventory
from stockpile.models import Bin
from stockpile.store import Store


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.add_bin(Bin("A-01", "WH-1", "TEA-0001", 10))
        self.store.add_bin(Bin("A-02", "WH-1", "TEA-0001", 5))
        self.store.add_bin(Bin("B-01", "WH-2", "TEA-0001", 7))

    def test_available_sums_the_warehouse_only(self):
        self.assertEqual(inventory.available(self.store, "WH-1", "TEA-0001"), 15)
        self.assertEqual(inventory.available(self.store, "WH-2", "TEA-0001"), 7)
        self.assertEqual(inventory.available(self.store, "WH-3", "TEA-0001"), 0)

    def test_receive_adds_units(self):
        self.assertEqual(inventory.receive(self.store, "A-02", 3), 8)
        with self.assertRaises(ValueError):
            inventory.receive(self.store, "A-02", 0)

    def test_adjust_records_the_count_and_returns_the_change(self):
        self.assertEqual(inventory.adjust(self.store, "A-01", 6), -4)
        self.assertEqual(self.store.bin("A-01").quantity, 6)
        with self.assertRaises(ValueError):
            inventory.adjust(self.store, "A-01", -1)


if __name__ == "__main__":
    unittest.main()
