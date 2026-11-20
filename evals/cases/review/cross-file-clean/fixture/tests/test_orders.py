import unittest
from decimal import Decimal

from storefront.cart import Cart
from storefront.catalog import Product
from storefront.orders import Account, place_order


def sample_cart():
    cart = Cart()
    cart.add(Product("PEN-01", "Gel pen", Decimal("1.99")), 3)
    return cart


class PlaceOrderTests(unittest.TestCase):
    def test_counts_orders(self):
        account = Account("cust-9", order_count=3)
        order = place_order(sample_cart(), account, "west")
        self.assertEqual((order.customer_id, account.order_count), ("cust-9", 4))

    def test_credits_the_points_it_reports(self):
        account = Account("cust-9", points=40, order_count=3)
        order = place_order(sample_cart(), account, "west")
        self.assertEqual(account.points, 40 + order.points_earned)

    def test_first_order_earns_more_than_a_repeat_order(self):
        first = place_order(sample_cart(), Account("cust-1"), "west")
        repeat = place_order(sample_cart(), Account("cust-2", order_count=1), "west")
        self.assertGreater(first.points_earned, repeat.points_earned)


if __name__ == "__main__":
    unittest.main()
