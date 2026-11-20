import unittest

from ledger.money import AmountError, format_amount, parse_amount


class MoneyTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_amount("1,234.50"), 123450)
        self.assertEqual(parse_amount(" -12 "), -1200)
        self.assertEqual(parse_amount("0.07"), 7)

    def test_too_many_decimals(self):
        with self.assertRaises(AmountError):
            parse_amount("1.005")

    def test_not_a_number(self):
        for text in ("", "abc", "NaN", "Infinity"):
            with self.subTest(text=text), self.assertRaises(AmountError):
                parse_amount(text)

    def test_format(self):
        self.assertEqual(format_amount(123450), "1,234.50")
        self.assertEqual(format_amount(-7), "-0.07")
        self.assertEqual(format_amount(0), "0.00")


if __name__ == "__main__":
    unittest.main()
