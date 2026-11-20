import unittest

from hookline.providers import Provider
from hookline.signatures import SignatureError, sign, verify

NOW = 1_780_000_000
BODY = b'{"id":"ev_1","type":"payment.settled"}'
KESTREL = Provider("kestrel", ("whsec_test",), "Kestrel-Signature")


def header(timestamp=NOW, secret="whsec_test", body=BODY):
    return {"Kestrel-Signature": f"t={timestamp},v1={sign(secret, timestamp, body)}"}


class VerifyTests(unittest.TestCase):
    def test_valid_signature(self):
        verify(KESTREL, header(), BODY, NOW)

    def test_wrong_secret(self):
        with self.assertRaisesRegex(SignatureError, "mismatch"):
            verify(KESTREL, header(secret="other"), BODY, NOW)

    def test_tampered_body(self):
        with self.assertRaisesRegex(SignatureError, "mismatch"):
            verify(KESTREL, header(), BODY.replace(b"settled", b"refunded"), NOW)

    def test_stale_timestamp(self):
        with self.assertRaisesRegex(SignatureError, "tolerance"):
            verify(KESTREL, header(timestamp=NOW - 301), BODY, NOW)

    def test_missing_header(self):
        with self.assertRaises(SignatureError):
            verify(KESTREL, {}, BODY, NOW)

    def test_header_name_is_case_insensitive(self):
        verify(KESTREL, {"kestrel-signature": header()["Kestrel-Signature"]}, BODY, NOW)

    def test_previous_secret_is_accepted_during_rotation(self):
        rotating = Provider("kestrel", ("whsec_new", "whsec_test"), "Kestrel-Signature")
        verify(rotating, header(), BODY, NOW)

    def test_sender_rotation_sends_two_signatures(self):
        value = f"t={NOW},v1={sign('whsec_old', NOW, BODY)},v1={sign('whsec_test', NOW, BODY)}"
        verify(KESTREL, {"Kestrel-Signature": value}, BODY, NOW)


if __name__ == "__main__":
    unittest.main()
