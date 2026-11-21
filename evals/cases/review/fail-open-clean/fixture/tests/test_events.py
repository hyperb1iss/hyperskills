import unittest

from hookline.events import Ledger, dispatch


class DispatchTests(unittest.TestCase):
    def test_event_needs_id_and_type(self):
        self.assertEqual(dispatch("kestrel", {"type": "payment.settled"}, Ledger())[0], 400)
        self.assertEqual(dispatch("kestrel", {"id": "ev_1"}, Ledger())[0], 400)

    def test_unhandled_type_is_ignored_and_not_recorded(self):
        ledger = Ledger()
        self.assertEqual(dispatch("kestrel", {"id": "ev_1", "type": "customer.created"}, ledger)[0], 202)
        self.assertEqual(ledger.processed, set())

    def test_ids_are_scoped_per_provider(self):
        ledger = Ledger()
        ledger.apply("other", "ev_1", "payment.settled", {})
        status, body = dispatch("kestrel", {"id": "ev_1", "type": "payment.settled"}, ledger)
        self.assertEqual((status, body["status"]), (200, "applied"))

    def test_data_is_recorded(self):
        ledger = Ledger()
        dispatch("kestrel", {"id": "ev_2", "type": "payment.refunded", "data": {"amount": 1200}}, ledger)
        self.assertEqual(ledger.entries[0]["data"], {"amount": 1200})


if __name__ == "__main__":
    unittest.main()
