import unittest
from datetime import date

from ledger.balances import balance
from ledger.invoices import InvoiceError, aging, apply_payment, issue_invoice, open_amount

from .support import make_store


class InvoiceTests(unittest.TestCase):
    def setUp(self):
        self.store = make_store()

    def test_issue_and_pay(self):
        invoice = issue_invoice(self.store, "Kettle Row Studio", date(2026, 1, 2), 90000)
        self.assertEqual(apply_payment(self.store, invoice.id, date(2026, 1, 20), 40000), 50000)
        self.assertEqual(open_amount(self.store, invoice.id), 50000)
        self.assertEqual(balance(self.store, "1200"), 50000)
        self.assertEqual(balance(self.store, "1000"), 40000)

    def test_overpayment_is_refused(self):
        invoice = issue_invoice(self.store, "Kettle Row Studio", date(2026, 1, 2), 1000)
        with self.assertRaises(InvoiceError):
            apply_payment(self.store, invoice.id, date(2026, 1, 3), 1001)

    def test_amounts_must_be_positive(self):
        with self.assertRaises(InvoiceError):
            issue_invoice(self.store, "Kettle Row Studio", date(2026, 1, 2), 0)

    def test_aging_buckets_and_later_payments(self):
        old = issue_invoice(self.store, "A", date(2025, 10, 1), 1000)
        issue_invoice(self.store, "B", date(2025, 12, 2), 2000)
        issue_invoice(self.store, "C", date(2025, 12, 31), 4000)
        apply_payment(self.store, old.id, date(2026, 1, 15), 1000)
        self.assertEqual(aging(self.store, date(2026, 1, 1)), {"0-30": 6000, "31-60": 0, "61-90": 0, "90+": 1000})
        self.assertEqual(aging(self.store, date(2026, 1, 31)), {"0-30": 0, "31-60": 6000, "61-90": 0, "90+": 0})

    def test_aging_boundaries(self):
        issue_invoice(self.store, "A", date(2026, 1, 1), 100)
        self.assertEqual(aging(self.store, date(2026, 1, 31))["0-30"], 100)
        self.assertEqual(aging(self.store, date(2026, 2, 1))["31-60"], 100)


if __name__ == "__main__":
    unittest.main()
