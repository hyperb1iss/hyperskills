import unittest

from routeplan.cache import GeoCache
from routeplan.client import GeocodeClient


class EmptyBackend:
    def geocode_batch(self, keys):
        return {}


class BoundedCacheProof(unittest.TestCase):
    def test_remembered_misses_stay_within_max_entries(self):
        cache = GeoCache(max_entries=50)
        client = GeocodeClient(EmptyBackend(), cache=cache, clock=lambda: 0)
        for n in range(500):
            client.lookup(f"{n} Unplaceable Lane")
        self.assertLessEqual(cache.stats()["unknown"], 50)
        self.assertIsNone(client.lookup("499 Unplaceable Lane"))


if __name__ == "__main__":
    unittest.main()
