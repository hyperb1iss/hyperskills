"""Proof for payout retries: a retried transfer must not be applied twice.

Run with the fixture root on sys.path. Fails on the defect fixture, passes on the clean one.
"""
import unittest
from datetime import datetime, timezone

from payouts.client import PayoutClient
from payouts.errors import GatewayTimeout
from payouts.models import Transfer
from payouts.retry import RetryPolicy


class LostReplyGateway:
    """Applies messages once per message_id, and loses the reply to the first one."""

    def __init__(self):
        self.replies = {}
        self.sent_ids = []
        self.payments = 0

    def send(self, message):
        message_id = message["message_id"]
        self.sent_ids.append(message_id)
        if message_id not in self.replies:
            self.payments += 1
            self.replies[message_id] = {
                "status": "accepted",
                "gateway_id": f"gw-{self.payments}",
                "message_id": message_id,
            }
        if len(self.sent_ids) == 1:
            raise GatewayTimeout("reply lost after the transfer was applied")
        return self.replies[message_id]


def submit_with_lost_reply():
    gateway = LostReplyGateway()
    client = PayoutClient(
        gateway,
        clock=lambda: datetime(2026, 3, 2, 9, 30, tzinfo=timezone.utc),
        retry=RetryPolicy(max_attempts=3),
        sleep=lambda seconds: None,
    )
    result = client.submit(Transfer(reference="INV-2001", account_id="acct-5", amount_cents=40_000))
    return gateway, result


class RetryIsIdempotent(unittest.TestCase):
    def test_transfer_is_paid_once(self):
        gateway, result = submit_with_lost_reply()
        self.assertEqual(result.status, "accepted")
        self.assertEqual(gateway.payments, 1)

    def test_every_attempt_reuses_the_message_id(self):
        gateway, _ = submit_with_lost_reply()
        self.assertEqual(len(gateway.sent_ids), 2)
        self.assertEqual(len(set(gateway.sent_ids)), 1)


if __name__ == "__main__":
    unittest.main()
