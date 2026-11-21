import unittest

from payouts.errors import GatewayTimeout, GatewayUnavailable, PayoutError
from payouts.transport import HttpTransport, raise_for_status


class FakeSession:
    def __init__(self, status=200, body=None, timeout=False):
        self.status = status
        self.body = body if body is not None else {"status": "accepted"}
        self.timeout = timeout
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append((url, json, timeout))
        if self.timeout:
            raise TimeoutError()
        return self.status, self.body


class RaiseForStatusTests(unittest.TestCase):
    def test_success_returns_body(self):
        self.assertEqual(raise_for_status(200, {"ok": 1}), {"ok": 1})

    def test_service_unavailable(self):
        with self.assertRaises(GatewayUnavailable):
            raise_for_status(503, {})

    def test_bad_gateway_is_unavailable(self):
        with self.assertRaises(GatewayUnavailable):
            raise_for_status(502, {})

    def test_gateway_timeout(self):
        with self.assertRaises(GatewayTimeout):
            raise_for_status(504, {})

    def test_other_errors(self):
        with self.assertRaises(PayoutError) as caught:
            raise_for_status(400, {})
        self.assertNotIsInstance(caught.exception, (GatewayUnavailable, GatewayTimeout))


class HttpTransportTests(unittest.TestCase):
    def test_posts_to_messages_endpoint(self):
        session = FakeSession()
        HttpTransport(session, "https://gateway.example.invalid/", timeout=3).send({"message_id": "m1"})
        self.assertEqual(session.calls, [("https://gateway.example.invalid/v2/messages", {"message_id": "m1"}, 3)])

    def test_timeout_maps_to_gateway_timeout(self):
        with self.assertRaises(GatewayTimeout):
            HttpTransport(FakeSession(timeout=True), "https://gateway.example.invalid").send({})


if __name__ == "__main__":
    unittest.main()
