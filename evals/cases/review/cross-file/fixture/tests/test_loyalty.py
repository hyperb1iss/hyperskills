import unittest

from storefront.loyalty import multiplier_for, points_after_purchase


class StubCart:
    def __init__(self, subtotal):
        self._subtotal = subtotal

    def subtotal(self):
        return self._subtotal


class LoyaltyTests(unittest.TestCase):
    def test_tier_multipliers(self):
        self.assertEqual([multiplier_for(t) for t in ("standard", "silver", "gold")], [1, 2, 3])

    def test_unknown_tier(self):
        with self.assertRaises(ValueError):
            multiplier_for("platinum")

    def test_signup_bonus_on_first_order(self):
        self.assertEqual(points_after_purchase(100, StubCart(0), first_order=True), 350)

    def test_no_bonus_after_first_order(self):
        self.assertEqual(points_after_purchase(100, StubCart(0)), 100)


if __name__ == "__main__":
    unittest.main()
