import unittest
from datetime import date
from decimal import Decimal

from ledger.accounts import create_account
from ledger.balances import balance, foreign_balance
from ledger.fx import record_rate
from ledger.journal import Entry, JournalError, Line, post, reverse
from ledger.periods import PeriodClosed

from .support import make_store


def sale(day, amount):
    return Entry(day, "Annual plan", [Line("1200", debit=amount), Line("4000", credit=amount)])


class PostTests(unittest.TestCase):
    def test_balanced_entry_is_stored(self):
        store = make_store()
        entry = post(store, sale(date(2026, 1, 5), 120000))
        self.assertEqual(len(store.select("lines", entry_id=entry.id)), 2)
        self.assertEqual(balance(store, "1200"), 120000)
        self.assertEqual(balance(store, "4000"), -120000)

    def test_unbalanced_entry_is_rejected(self):
        store = make_store()
        lines = [Line("5000", debit=900), Line("1000", credit=800)]
        with self.assertRaisesRegex(JournalError, "does not balance"):
            post(store, Entry(date(2026, 1, 5), "Hosting", lines))
        self.assertEqual(store.table("entries"), [])

    def test_unknown_account(self):
        with self.assertRaises(ValueError):
            post(make_store(), Entry(date(2026, 1, 5), "x", [Line("9999", debit=1), Line("1000", credit=1)]))

    def test_a_line_is_a_debit_or_a_credit(self):
        for kwargs in ({}, {"debit": 1, "credit": 1}, {"debit": -5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(JournalError):
                Line("1000", **kwargs)

    def test_closed_period_rejects_posting(self):
        store = make_store()
        store.insert("periods", {"end": "2026-01-31"})
        with self.assertRaises(PeriodClosed):
            post(store, sale(date(2026, 1, 31), 100))
        post(store, sale(date(2026, 2, 1), 100))

    def test_reversal_mirrors_the_entry(self):
        store = make_store()
        entry = post(store, sale(date(2026, 1, 5), 5000))
        reverse(store, entry.id, date(2026, 1, 9))
        self.assertEqual(balance(store, "1200"), 0)
        self.assertEqual(balance(store, "4000"), 0)


def euro_store():
    store = make_store()
    create_account(store, "1010", "Euro bank", "asset", "EUR")
    create_account(store, "1210", "Euro receivables", "asset", "EUR")
    record_rate(store, "EUR", date(2026, 1, 1), Decimal("1.0850"))
    record_rate(store, "EUR", date(2026, 2, 1), Decimal("1.1000"))
    return store


class MultiCurrencyTests(unittest.TestCase):
    def test_foreign_line_carries_its_base_amount(self):
        store = euro_store()
        post(store, Entry(date(2026, 1, 15), "Euro customer", [Line("1210", debit=100000), Line("4000", credit=108500)]))
        self.assertEqual((foreign_balance(store, "1210"), balance(store, "1210")), (100000, 108500))

    def test_conversion_rounding_is_booked(self):
        store = euro_store()
        lines = [Line("1210", debit=5), Line("1210", debit=5), Line("1010", credit=10)]
        entry = post(store, Entry(date(2026, 1, 15), "Split", lines))
        rounding = store.select("lines", entry_id=entry.id, account="7990")
        self.assertEqual([(row["debit"], row["credit"]) for row in rounding], [(1, 0)])
        self.assertEqual(sum(balance(store, code) for code in ("1210", "1010", "7990")), 0)

    def test_mixed_entry_must_balance_in_base(self):
        store = euro_store()
        lines = [Line("1010", debit=100000), Line("1000", credit=100000)]
        with self.assertRaisesRegex(JournalError, "does not balance in USD"):
            post(store, Entry(date(2026, 1, 15), "Transfer", lines))

    def test_reversal_uses_the_original_base_amounts(self):
        store = euro_store()
        entry = post(store, Entry(date(2026, 1, 15), "Euro sale", [Line("1210", debit=100000), Line("4000", credit=108500)]))
        reverse(store, entry.id, date(2026, 2, 10))
        self.assertEqual((balance(store, "1210"), foreign_balance(store, "1210")), (0, 0))

if __name__ == "__main__":
    unittest.main()
