import unittest
from datetime import date
from decimal import Decimal

from ledger.fx import MissingRate, RateTable, to_base
from ledger.money import AmountError, format_amount, parse_amount


class RateTableTests(unittest.TestCase):
    def setUp(self):
        self.rates = RateTable()
        self.rates.add("EUR", date(2026, 1, 1), Decimal("1.0850"))
        self.rates.add("EUR", date(2026, 2, 1), Decimal("1.1000"))

    def test_rate_carries_forward(self):
        self.assertEqual(self.rates.find("EUR", date(2026, 1, 20)), Decimal("1.0850"))
        self.assertEqual(self.rates.find("EUR", date(2026, 3, 15)), Decimal("1.1000"))

    def test_no_rate_before_the_first_one(self):
        self.assertIsNone(self.rates.find("EUR", date(2025, 12, 31)))
        with self.assertRaises(MissingRate):
            self.rates.rate_on("GBP", date(2026, 1, 20))

    def test_closing_rate_must_be_dated_on_the_day(self):
        self.assertEqual(self.rates.closing_rate("EUR", date(2026, 2, 1)), Decimal("1.1000"))
        self.assertIsNone(self.rates.closing("EUR", date(2026, 1, 31)))
        with self.assertRaises(MissingRate):
            self.rates.closing_rate("EUR", date(2026, 1, 31))

    def test_a_second_rate_for_a_day_replaces_the_first(self):
        self.rates.add("EUR", date(2026, 2, 1), Decimal("1.0990"))
        self.assertEqual(self.rates.closing("EUR", date(2026, 2, 1)), Decimal("1.0990"))

    def test_to_base_rounds_half_even(self):
        self.assertEqual(to_base(self.rates, 5, "EUR", date(2026, 1, 20)), 5)
        self.assertEqual(to_base(self.rates, 100000, "EUR", date(2026, 1, 20)), 108500)
        self.assertEqual(to_base(self.rates, 4200, "USD", date(2026, 1, 20)), 4200)


class CurrencyAmountTests(unittest.TestCase):
    def test_yen_has_no_minor_unit(self):
        self.assertEqual(parse_amount("1,500", "JPY"), 1500)
        self.assertEqual(format_amount(1500, "JPY"), "1,500")
        with self.assertRaises(AmountError):
            parse_amount("1.5", "JPY")

if __name__ == "__main__":
    unittest.main()
