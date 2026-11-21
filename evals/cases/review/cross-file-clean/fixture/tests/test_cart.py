import unittest
from decimal import Decimal

from storefront.cart import Cart, CartError
from storefront.catalog import Catalog, Product, UnknownProduct

PEN = Product("PEN-01", "Gel pen", Decimal("1.99"), weight_grams=12)
NOTEBOOK = Product("NB-A5", "A5 notebook", Decimal("12.50"), weight_grams=310)


class CartTests(unittest.TestCase):
    def test_subtotal(self):
        cart = Cart()
        cart.add(PEN, 3)
        cart.add(NOTEBOOK)
        self.assertEqual(cart.subtotal(), 1847)

    def test_adding_same_product_merges_lines(self):
        cart = Cart()
        cart.add(PEN)
        cart.add(PEN, 2)
        self.assertEqual([(line.product.sku, line.quantity) for line in cart.lines], [("PEN-01", 3)])

    def test_quantity_limit(self):
        cart = Cart()
        cart.add(PEN, 98)
        with self.assertRaises(CartError):
            cart.add(PEN, 2)

    def test_remove_and_weight(self):
        cart = Cart()
        cart.add(PEN, 2)
        cart.add(NOTEBOOK)
        cart.remove("PEN-01")
        self.assertEqual(cart.weight_grams(), 310)


class CatalogTests(unittest.TestCase):
    def test_from_rows_parses_prices(self):
        catalog = Catalog.from_rows([("PEN-01", "Gel pen", "1.99", "12")])
        self.assertEqual(catalog.get("PEN-01").price, Decimal("1.99"))
        self.assertEqual(catalog.get("PEN-01").price_cents, 199)
        self.assertIn("PEN-01", catalog)

    def test_unknown_product(self):
        with self.assertRaises(UnknownProduct):
            Catalog().get("NOPE")


if __name__ == "__main__":
    unittest.main()
