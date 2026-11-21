import unittest

from digests.mailer import (
    InvalidAddress, Message, RecordingTransport, RelayTransport, TransportError, parse_address,
)


def message(to="ada@example.com", body="hello"):
    return Message(to=to, subject="Hi", body=body, sender="notify@example.invalid", category="immediate")


class ParseAddressTests(unittest.TestCase):
    def test_strips_whitespace(self):
        self.assertEqual(parse_address("  ada@example.com "), "ada@example.com")

    def test_rejects_unusable_addresses(self):
        for raw in ("", None, "ada", "ada@example", "ada@example.com, ben@example.com", "a b@example.com"):
            with self.subTest(raw=raw), self.assertRaises(InvalidAddress):
                parse_address(raw)


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.envelopes = []

    def submit(self, envelope):
        if self.error:
            raise self.error
        self.envelopes.append(envelope)


class TransportTests(unittest.TestCase):
    def test_recording_transport_keeps_messages(self):
        transport = RecordingTransport()
        transport.send(message())
        self.assertEqual([m.to for m in transport.sent], ["ada@example.com"])

    def test_recording_transport_refuses_listed_addresses(self):
        with self.assertRaises(TransportError):
            RecordingTransport(refuse={"ada@example.com"}).send(message())

    def test_relay_submits_envelope(self):
        client = FakeClient()
        RelayTransport(client).send(message())
        self.assertEqual(client.envelopes[0]["to"], "ada@example.com")
        self.assertEqual(client.envelopes[0]["category"], "immediate")

    def test_relay_connection_errors_become_transport_errors(self):
        with self.assertRaises(TransportError):
            RelayTransport(FakeClient(error=TimeoutError("slow"))).send(message())

    def test_relay_rejects_oversized_body(self):
        with self.assertRaises(TransportError):
            RelayTransport(FakeClient(), max_body_bytes=10).send(message(body="x" * 11))


if __name__ == "__main__":
    unittest.main()
