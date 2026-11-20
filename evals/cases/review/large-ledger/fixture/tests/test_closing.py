import unittest
from datetime import date

from ledger.closing import close_period
from ledger.journal import Entry, Line, post
from ledger.periods import PeriodClosed, closed_through, reopen

from .support import make_store


class CloseTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        post(self.store, Entry(date(2026, 1, 3), "Seed", [Line("1000", debit=500000), Line("3000", credit=500000)]))

    def test_close_records_the_period(self):
        balances = close_period(self.store, date(2026, 1, 31))
        self.assertEqual(balances["1000"], 500000)
        self.assertEqual(closed_through(self.store), date(2026, 1, 31))

    def test_cannot_close_twice(self):
        close_period(self.store, date(2026, 1, 31))
        with self.assertRaises(PeriodClosed):
            close_period(self.store, date(2026, 1, 15))

    def test_reopen_latest_only(self):
        close_period(self.store, date(2026, 1, 31))
        close_period(self.store, date(2026, 2, 28))
        with self.assertRaises(PeriodClosed):
            reopen(self.store, date(2026, 1, 31))
        reopen(self.store, date(2026, 2, 28))
        self.assertEqual(closed_through(self.store), date(2026, 1, 31))


if __name__ == "__main__":
    unittest.main()
