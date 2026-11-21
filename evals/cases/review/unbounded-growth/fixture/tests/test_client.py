import unittest

from routeplan.client import GeocodeClient
from routeplan.normalize import normalize


class FakeBackend:
    def __init__(self, known):
        self.known = known
        self.calls = []

    def geocode_batch(self, keys):
        self.calls.append(list(keys))
        return {key: self.known[key] for key in keys if key in self.known}


class ClientTests(unittest.TestCase):
    def test_equivalent_spellings_share_a_lookup(self):
        backend = FakeBackend({"12 harbor st": (1.0, 2.0)})
        client = GeocodeClient(backend, clock=lambda: 0)
        self.assertEqual(client.lookup("12 Harbor Street"), (1.0, 2.0))
        self.assertEqual(client.lookup("12 harbor st."), (1.0, 2.0))
        self.assertEqual(len(backend.calls), 1)

    def test_unknown_address(self):
        client = GeocodeClient(FakeBackend({}), clock=lambda: 0)
        self.assertIsNone(client.lookup("nowhere"))

    def test_batch_sends_each_miss_once(self):
        backend = FakeBackend({"12 harbor st": (1.0, 2.0), "9 mill rd": (3.0, 4.0)})
        client = GeocodeClient(backend, clock=lambda: 0)
        addresses = ["12 Harbor St", "12 Harbor St Apt 4", "9 Mill Rd", "nowhere"]
        self.assertEqual(client.lookup_many(addresses)["12 Harbor St Apt 4"], (1.0, 2.0))
        self.assertEqual(client.lookup_many(addresses)["nowhere"], None)
        self.assertEqual(backend.calls, [["12 harbor st", "9 mill rd", "nowhere"]])

    def test_normalize(self):
        self.assertEqual(normalize("  4 North Mill Road, "), "4 n mill rd")
        self.assertEqual(normalize("4 Mill Rd #12"), normalize("4 mill road, suite 3"))


if __name__ == "__main__":
    unittest.main()
