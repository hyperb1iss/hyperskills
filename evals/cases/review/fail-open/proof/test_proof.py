import unittest

from hookline.events import Ledger
from hookline.handlers import handle
from hookline.providers import Provider, load_providers
from hookline.signatures import SignatureError, verify

NOW = 1_780_000_000
BODY = b'{"id":"ev_9","type":"payment.settled","data":{"amount":500000}}'
ENV = {"KESTREL_SIGNING_SECRET": "whsec_kestrel", "OSPREY_SIGNING_SECRET": "whsec_osprey"}


class UnsignedRequestProof(unittest.TestCase):
    def test_header_without_a_signature_is_rejected(self):
        provider = Provider("kestrel", ("whsec_kestrel",), "Kestrel-Signature")
        with self.assertRaises(SignatureError):
            verify(provider, {"Kestrel-Signature": f"t={NOW}"}, BODY, NOW)

    def test_unsigned_event_never_reaches_the_ledger(self):
        ledger = Ledger()
        request = {"path": "/hooks/kestrel", "headers": {"Kestrel-Signature": f"t={NOW}"}, "body": BODY}
        status, _ = handle(request, load_providers(ENV), ledger, clock=lambda: NOW)
        self.assertEqual(status, 401)
        self.assertEqual(ledger.entries, [])


if __name__ == "__main__":
    unittest.main()
