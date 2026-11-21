import unittest
from datetime import datetime, timezone

from payouts.client import PayoutClient
from payouts.errors import GatewayTimeout, GatewayUnavailable, PayoutError, Rejected
from payouts.models import Transfer
from payouts.retry import RetryPolicy


def fixed_clock():
    return datetime(2026, 3, 2, 9, 30, tzinfo=timezone.utc)


class FakeGateway:
    """Answers like the gateway: one reply per message_id."""

    def __init__(self, failures=(), status="accepted"):
        self.failures = list(failures)
        self.status = status
        self.sent = []
        self.replies = {}

    def send(self, message):
        self.sent.append(message)
        if self.failures:
            raise self.failures.pop(0)
        message_id = message["message_id"]
        if message_id not in self.replies:
            self.replies[message_id] = {
                "status": self.status,
                "code": "account_closed",
                "gateway_id": f"gw-{len(self.replies) + 1}",
                "message_id": message_id,
            }
        return self.replies[message_id]


def make_client(gateway, sleeps=None):
    return PayoutClient(
        gateway,
        clock=fixed_clock,
        retry=RetryPolicy(max_attempts=3),
        sleep=sleeps.append if sleeps is not None else (lambda seconds: None),
    )


TRANSFER = Transfer(reference="INV-1042", account_id="acct-77", amount_cents=12_500)


class SubmitTests(unittest.TestCase):
    def test_accepted_transfer(self):
        result = make_client(FakeGateway()).submit(TRANSFER)
        self.assertEqual(result.status, "accepted")

    def test_message_carries_transfer_fields(self):
        gateway = FakeGateway()
        make_client(gateway).submit(TRANSFER)
        body = gateway.sent[0]["transfer"]
        self.assertEqual(body, {"reference": "INV-1042", "account": "acct-77", "amount": 12_500, "currency": "USD"})
        self.assertEqual(gateway.sent[0]["sent_at"], "2026-03-02T09:30:00+00:00")

    def test_rejection_is_raised(self):
        gateway = FakeGateway(status="rejected")
        with self.assertRaises(Rejected):
            make_client(gateway).submit(TRANSFER)
        self.assertEqual(len(gateway.sent), 1)

    def test_retries_transient_failures_with_backoff(self):
        gateway = FakeGateway(failures=[GatewayUnavailable("503"), GatewayTimeout("504")])
        sleeps = []
        result = make_client(gateway, sleeps).submit(TRANSFER)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(len(gateway.sent), 3)
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_gives_up_after_last_attempt(self):
        gateway = FakeGateway(failures=[GatewayUnavailable("503")] * 3)
        sleeps = []
        with self.assertRaises(GatewayUnavailable):
            make_client(gateway, sleeps).submit(TRANSFER)
        self.assertEqual(len(gateway.sent), 3)
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_other_errors_are_not_retried(self):
        gateway = FakeGateway(failures=[PayoutError("gateway answered 500")])
        with self.assertRaises(PayoutError):
            make_client(gateway).submit(TRANSFER)
        self.assertEqual(len(gateway.sent), 1)


class SubmitAllTests(unittest.TestCase):
    def test_collects_results_and_errors(self):
        gateway = FakeGateway(failures=[PayoutError("gateway answered 500")])
        client = make_client(gateway)
        second = Transfer(reference="INV-1043", account_id="acct-78", amount_cents=900)
        results = client.submit_all([TRANSFER, second])
        self.assertIsInstance(results["INV-1042"], PayoutError)
        self.assertEqual(results["INV-1043"].status, "accepted")


if __name__ == "__main__":
    unittest.main()
