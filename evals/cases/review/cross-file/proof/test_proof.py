"""Proof for loyalty points after the switch to cents: one point per whole dollar.

Run with the fixture root on sys.path. Fails on the defect fixture, passes on the clean one.
"""
import unittest
from decimal import Decimal

from storefront.cart import Cart
from storefront.catalog import Product
from storefront.orders import Account, place_order


def tote_cart():
    cart = Cart()
    cart.add(Product("BAG-1", "Tote bag", Decimal("42.50")))
    return cart


class PointsFollowWholeDollars(unittest.TestCase):
    def test_standard_order_earns_one_point_per_dollar(self):
        account = Account("cust-1", order_count=2)
        order = place_order(tote_cart(), account, "west")
        self.assertEqual(order.points_earned, 42)

    def test_gold_order_credits_tripled_dollar_points(self):
        account = Account("cust-2", tier="gold", order_count=5)
        place_order(tote_cart(), account, "west")
        self.assertEqual(account.points, 126)


if __name__ == "__main__":
    unittest.main()
