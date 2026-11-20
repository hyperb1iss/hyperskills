import unittest
from decimal import Decimal

from storefront.cart import Cart
from storefront.catalog import Product
from storefront.invoice import build_invoice, format_money
from storefront.orders import Account, place_order
from storefront.tax import UnknownRegion, tax_for

PEN = Product("PEN-01", "Gel pen", Decimal("1.99"))
NOTEBOOK = Product("NB-A5", "A5 notebook", Decimal("12.50"))


def sample_cart():
    cart = Cart()
    cart.add(PEN, 3)
    cart.add(NOTEBOOK)
    return cart


class TaxTests(unittest.TestCase):
    def test_rounds_half_up_to_the_cent(self):
        self.assertEqual(tax_for(1000, "north"), 73)

    def test_unknown_region(self):
        with self.assertRaises(UnknownRegion):
            tax_for(1, "lunar")


class InvoiceTests(unittest.TestCase):
    def test_totals(self):
        invoice = build_invoice(sample_cart(), "north")
        self.assertEqual((invoice.subtotal, invoice.tax, invoice.total), (1847, 134, 1981))

    def test_render(self):
        text = build_invoice(sample_cart(), "east").render()
        self.assertIn("  3 x Gel pen", text)
        self.assertIn("$5.97", text)
        self.assertTrue(text.splitlines()[-1].endswith("$20.09"))

    def test_empty_cart_is_rejected(self):
        with self.assertRaises(ValueError):
            build_invoice(Cart(), "north")

    def test_format_money(self):
        self.assertEqual(format_money(123456), "$1,234.56")
        self.assertEqual(format_money(-5), "-$0.05")


class PlaceOrderTests(unittest.TestCase):
    def test_counts_orders_and_credits_points(self):
        account = Account("cust-9", points=40, order_count=3)
        order = place_order(sample_cart(), account, "west")
        self.assertEqual(order.invoice.total, 1847)
        self.assertEqual(account.order_count, 4)
        self.assertEqual(account.points, 40 + order.points_earned)


if __name__ == "__main__":
    unittest.main()
