import unittest
from datetime import datetime, timezone

from payouts.errors import Rejected
from payouts.messages import parse_reply, transfer_message
from payouts.models import Transfer


class TransferMessageTests(unittest.TestCase):
    def test_shape(self):
        transfer = Transfer(reference="R-1", account_id="acct-1", amount_cents=500, currency="EUR")
        message = transfer_message(transfer, datetime(2026, 1, 5, tzinfo=timezone.utc))
        self.assertEqual(message["kind"], "transfer.create")
        self.assertEqual(message["transfer"]["currency"], "EUR")
        self.assertEqual(len(message["message_id"]), 32)


class ParseReplyTests(unittest.TestCase):
    def test_accepted(self):
        result = parse_reply({"status": "pending", "gateway_id": "gw-9", "message_id": "m"})
        self.assertEqual((result.status, result.gateway_id), ("pending", "gw-9"))

    def test_rejected(self):
        with self.assertRaises(Rejected) as caught:
            parse_reply({"status": "rejected", "code": "limit_exceeded"})
        self.assertEqual(caught.exception.code, "limit_exceeded")

    def test_unknown_status(self):
        with self.assertRaises(ValueError):
            parse_reply({"status": "queued"})


class TransferValidationTests(unittest.TestCase):
    def test_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError):
            Transfer(reference="R-1", account_id="a", amount_cents=0)

    def test_rejects_long_reference(self):
        with self.assertRaises(ValueError):
            Transfer(reference="R" * 36, account_id="a", amount_cents=1)


if __name__ == "__main__":
    unittest.main()
