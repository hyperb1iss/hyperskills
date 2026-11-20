import unittest

from stockroom.auth import can_access_warehouse, visible_warehouses
from stockroom.models import Principal


class AuthTests(unittest.TestCase):
    def test_scoped_key(self):
        clerk = Principal("k-1", frozenset({"stock:read"}), frozenset({"east"}))
        self.assertTrue(can_access_warehouse(clerk, "east"))
        self.assertFalse(can_access_warehouse(clerk, "west"))
        self.assertFalse(can_access_warehouse(clerk, None))

    def test_admin_sees_everything(self):
        admin = Principal("k-2", frozenset({"admin"}))
        self.assertTrue(can_access_warehouse(admin, "west"))
        self.assertTrue(admin.has_role("stock:write"))

    def test_unscoped_key_sees_nothing(self):
        bare = Principal("k-3", frozenset({"stock:read"}))
        self.assertEqual(visible_warehouses(bare, ["east", "west"]), [])

    def test_visible_keeps_order(self):
        clerk = Principal("k-4", frozenset(), frozenset({"west", "east"}))
        self.assertEqual(visible_warehouses(clerk, ["west", "north", "east"]), ["west", "east"])


if __name__ == "__main__":
    unittest.main()
