import unittest

from boxoffice import pricing


class PricingTests(unittest.TestCase):
    def test_fee_is_clamped(self):
        self.assertEqual(pricing.service_fee(500), pricing.MIN_SERVICE_FEE)
        self.assertEqual(pricing.service_fee(5000), 300)
        self.assertEqual(pricing.service_fee(50000), pricing.MAX_SERVICE_FEE)

    def test_free_tickets_have_no_fee(self):
        self.assertEqual(pricing.quote(0, 0.1).total, 0)

    def test_quote_total(self):
        q = pricing.quote(4000, 0.08)
        self.assertEqual((q.service_fee, q.tax, q.total), (240, 339, 4579))

    def test_refund_window(self):
        q = pricing.quote(4000, 0.08)
        self.assertEqual(pricing.refund_amount(q, 7), q.total)
        self.assertEqual(pricing.refund_amount(q, 1), 4000)
        self.assertEqual(pricing.refund_amount(q, 0), 0)

    def test_group_discount_starts_at_eight(self):
        self.assertEqual(pricing.group_discount(4000, 7), 4000)
        self.assertEqual(pricing.group_discount(4000, 8), 3600)
        with self.assertRaises(ValueError):
            pricing.group_discount(4000, 0)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            pricing.quote(-1, 0.08)


if __name__ == "__main__":
    unittest.main()
