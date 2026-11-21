import unittest

from hookline import reports


def entry(provider, kind, amount=None, event="ev"):
    data = {} if amount is None else {"amount": amount}
    return {"provider": provider, "event": event, "kind": kind, "data": data}


class ReportTests(unittest.TestCase):
    def test_refunds_subtract(self):
        entries = [entry("kestrel", "payment.settled", 5000), entry("kestrel", "payment.refunded", 1250)]
        self.assertEqual(reports.net_by_provider(entries), {"kestrel": 3750})

    def test_missing_amount_counts_as_zero(self):
        self.assertEqual(reports.net_by_provider([entry("kestrel", "payment.settled")]), {"kestrel": 0})

    def test_non_integer_amount_is_an_error(self):
        with self.assertRaises(ValueError):
            reports.net_by_provider([entry("kestrel", "payment.settled", "12.50")])

    def test_counts(self):
        entries = [entry("kestrel", "payment.settled", 1), entry("kestrel", "payment.settled", 2)]
        self.assertEqual(reports.counts_by_kind(entries), {("kestrel", "payment.settled"): 2})

    def test_summary_formats_negative_totals(self):
        entries = [entry("kestrel", "payment.refunded", 705), entry("heron", "payment.settled", 100000)]
        self.assertEqual(reports.format_summary(entries), "heron: 1000.00\nkestrel: -7.05")


if __name__ == "__main__":
    unittest.main()
