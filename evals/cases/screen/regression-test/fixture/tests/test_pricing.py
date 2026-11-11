import unittest

import pricing


class OrderTotalTests(unittest.TestCase):
    def test_small_order_pays_full_price(self):
        self.assertEqual(pricing.order_total(5, 1), 5)

    def test_large_order_gets_discount(self):
        self.assertEqual(pricing.order_total(5, 20), 90.0)


if __name__ == "__main__":
    unittest.main()
