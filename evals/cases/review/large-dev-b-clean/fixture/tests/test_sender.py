import unittest

from digests.mailer import Message, RecordingTransport
from digests.sender import FAILED, SENT, send_batch


def message(to):
    return Message(to=to, subject="3 updates today", body="...", sender="digest@example.invalid", category="digest-daily")


class SendBatchTests(unittest.TestCase):
    def test_sends_every_message_in_order(self):
        transport = RecordingTransport()
        results = send_batch(transport, [("u-ada", message("ada@example.com")), ("u-ben", message("ben@example.com"))])
        self.assertEqual([m.to for m in transport.sent], ["ada@example.com", "ben@example.com"])
        self.assertEqual([(r.key, r.status) for r in results], [("u-ada", SENT), ("u-ben", SENT)])

    def test_relay_failure_fails_only_that_message(self):
        transport = RecordingTransport(refuse={"ada@example.com"})
        results = send_batch(transport, [("u-ada", message("ada@example.com")), ("u-ben", message("ben@example.com"))])
        self.assertEqual([r.status for r in results], [FAILED, SENT])
        self.assertIn("refused", results[0].detail)
        self.assertEqual([m.to for m in transport.sent], ["ben@example.com"])

    def test_addresses_are_normalized_before_sending(self):
        transport = RecordingTransport()
        send_batch(transport, [("u-ada", message("  ada@example.com "))])
        self.assertEqual(transport.sent[0].to, "ada@example.com")


if __name__ == "__main__":
    unittest.main()
