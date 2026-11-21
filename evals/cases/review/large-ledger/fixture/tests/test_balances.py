import unittest
from datetime import date

from ledger.balances import balance, format_trial_balance, natural_balance, trial_balance
from ledger.journal import Entry, Line, post

from .support import make_store


class BalanceTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        post(self.store, Entry(date(2026, 1, 3), "Seed", [Line("1000", debit=500000), Line("3000", credit=500000)]))
        post(self.store, Entry(date(2026, 1, 20), "Hosting", [Line("5000", debit=12000), Line("1000", credit=12000)]))

    def test_balance_through_a_date(self):
        self.assertEqual(balance(self.store, "1000", date(2026, 1, 10)), 500000)
        self.assertEqual(balance(self.store, "1000"), 488000)

    def test_natural_balance(self):
        self.assertEqual(natural_balance(self.store, "3000"), 500000)
        self.assertEqual(natural_balance(self.store, "5000"), 12000)

    def test_trial_balance_nets_to_zero(self):
        balances = trial_balance(self.store)
        self.assertEqual(sum(balances.values()), 0)
        self.assertEqual(balances["4000"], 0)

    def test_format(self):
        text = format_trial_balance(self.store)
        self.assertIn("1000  Operating bank", text)
        self.assertIn("4,880.00", text)


if __name__ == "__main__":
    unittest.main()
