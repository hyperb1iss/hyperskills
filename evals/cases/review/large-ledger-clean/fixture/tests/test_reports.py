import unittest
from datetime import date

from ledger.journal import Entry, Line, post
from ledger.reports import format_income_statement, income_statement, period_total

from .support import make_store


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        for day, amount in ((date(2025, 12, 30), 1000), (date(2026, 1, 10), 250000), (date(2026, 2, 1), 7000)):
            post(self.store, Entry(day, "Plan", [Line("1200", debit=amount), Line("4000", credit=amount)]))
        post(self.store, Entry(date(2026, 1, 12), "Hosting", [Line("5000", debit=40000), Line("2000", credit=40000)]))

    def test_period_total_excludes_other_months(self):
        self.assertEqual(period_total(self.store, "4000", date(2026, 1, 1), date(2026, 1, 31)), 250000)

    def test_income_statement(self):
        statement = income_statement(self.store, date(2026, 1, 1), date(2026, 1, 31))
        self.assertEqual(statement["net"], 210000)
        self.assertEqual(statement["expenses"]["5100"], 0)

    def test_format_hides_empty_accounts(self):
        text = format_income_statement(self.store, date(2026, 1, 1), date(2026, 1, 31))
        self.assertIn("4000 Subscription revenue", text)
        self.assertNotIn("Contractors", text)
        self.assertTrue(text.endswith("2,100.00"))


if __name__ == "__main__":
    unittest.main()
