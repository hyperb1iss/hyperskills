import json
import unittest

from hookline.events import Ledger
from hookline.handlers import handle
from hookline.providers import load_providers
from hookline.signatures import sign

NOW = 1_780_000_000
ENV = {"KESTREL_SIGNING_SECRET": "whsec_kestrel", "OSPREY_SIGNING_SECRET": "whsec_osprey_old, whsec_osprey"}


def request(provider, event, secret, header):
    body = json.dumps(event).encode()
    return {
        "path": f"/hooks/{provider}",
        "headers": {header: f"t={NOW},v1={sign(secret, NOW, body)}"},
        "body": body,
    }


class HandleTests(unittest.TestCase):
    def setUp(self):
        self.providers = load_providers(ENV)
        self.ledger = Ledger()

    def call(self, req):
        return handle(req, self.providers, self.ledger, clock=lambda: NOW)

    def test_settled_payment_is_applied_once(self):
        req = request("kestrel", {"id": "ev_1", "type": "payment.settled"}, "whsec_kestrel", "Kestrel-Signature")
        self.assertEqual(self.call(req), (200, {"status": "applied"}))
        self.assertEqual(self.call(req), (200, {"status": "duplicate"}))
        self.assertEqual(len(self.ledger.entries), 1)

    def test_osprey_transfer_is_applied(self):
        req = request("osprey", {"id": "tr_7", "type": "transfer.completed"}, "whsec_osprey", "osprey-signature")
        self.assertEqual(self.call(req), (200, {"status": "applied"}))
        self.assertEqual(self.ledger.entries[0]["provider"], "osprey")

    def test_unknown_provider(self):
        req = request("heron", {"id": "ev_1", "type": "x"}, "s", "Heron-Signature")
        self.assertEqual(self.call(req)[0], 404)

    def test_bad_signature_is_rejected(self):
        req = request("kestrel", {"id": "ev_1", "type": "payment.settled"}, "wrong", "Kestrel-Signature")
        self.assertEqual(self.call(req)[0], 401)
        self.assertEqual(self.ledger.entries, [])

    def test_missing_secret_fails_at_startup(self):
        with self.assertRaises(KeyError):
            load_providers({"KESTREL_SIGNING_SECRET": "whsec_kestrel", "OSPREY_SIGNING_SECRET": " , "})


if __name__ == "__main__":
    unittest.main()
