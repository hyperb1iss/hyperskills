import unittest
from datetime import date
from decimal import Decimal

from ledger.accounts import create_account
from ledger.balances import balance, foreign_balance
from ledger.closing import close_period
from ledger.fx import record_rate
from ledger.journal import Entry, Line, post
from ledger.revaluation import revalue

from .support import make_store

JAN_31 = date(2026, 1, 31)


def euro_books():
    store = make_store()
    create_account(store, "1010", "Euro bank", "asset", "EUR")
    create_account(store, "2010", "Euro payables", "liability", "EUR")
    record_rate(store, "EUR", date(2026, 1, 1), Decimal("1.0800"))
    post(store, Entry(date(2026, 1, 10), "Fund euro account", [Line("1010", debit=1000000), Line("3000", credit=1080000)]))
    return store


class RevaluationTests(unittest.TestCase):
    def test_gain_when_the_currency_strengthens(self):
        store = euro_books()
        record_rate(store, "EUR", JAN_31, Decimal("1.1000"))
        result = revalue(store, JAN_31)
        self.assertEqual(result.adjustments, {"1010": 20000})
        self.assertEqual((balance(store, "1010"), foreign_balance(store, "1010")), (1100000, 1000000))
        self.assertEqual(balance(store, "7910"), -20000)

    def test_liabilities_offset_assets(self):
        store = euro_books()
        post(store, Entry(date(2026, 1, 12), "Supplier bill", [Line("5100", debit=216000), Line("2010", credit=200000)]))
        record_rate(store, "EUR", JAN_31, Decimal("1.1000"))
        result = revalue(store, JAN_31)
        self.assertEqual(result.adjustments, {"1010": 20000, "2010": -4000})
        self.assertEqual(balance(store, "7910"), -16000)

    def test_running_twice_posts_once(self):
        store = euro_books()
        record_rate(store, "EUR", JAN_31, Decimal("1.1000"))
        self.assertIsNotNone(revalue(store, JAN_31).entry_id)
        self.assertIsNone(revalue(store, JAN_31).entry_id)

    def test_close_revalues_then_locks(self):
        store = euro_books()
        record_rate(store, "EUR", JAN_31, Decimal("1.1000"))
        close_period(store, JAN_31)
        self.assertIsNotNone(store.one("periods", end="2026-01-31")["revaluation_entry"])
        self.assertEqual(balance(store, "1010"), 1100000)


if __name__ == "__main__":
    unittest.main()
