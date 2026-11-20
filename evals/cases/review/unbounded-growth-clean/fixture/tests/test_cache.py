import unittest

from routeplan.cache import GeoCache


class CacheTests(unittest.TestCase):
    def test_hit_and_miss_counts(self):
        cache = GeoCache()
        self.assertIsNone(cache.get("a", 0))
        cache.put("a", (1.0, 2.0), 0)
        self.assertEqual(cache.get("a", 10), (1.0, 2.0))
        self.assertEqual((cache.hits, cache.misses), (1, 1))

    def test_entries_expire(self):
        cache = GeoCache(ttl=60)
        cache.put("a", (1.0, 2.0), 0)
        self.assertIsNone(cache.get("a", 60))
        self.assertEqual(len(cache), 0)

    def test_least_recently_used_is_evicted(self):
        cache = GeoCache(max_entries=2)
        cache.put("a", (0.0, 0.0), 0)
        cache.put("b", (0.0, 1.0), 0)
        cache.get("a", 1)
        cache.put("c", (0.0, 2.0), 1)
        self.assertIsNone(cache.get("b", 2))
        self.assertEqual(len(cache), 2)

    def test_unknown_addresses_are_remembered_until_they_expire(self):
        cache = GeoCache(unknown_ttl=60)
        cache.put_unknown("nowhere", 0)
        self.assertIsNotNone(cache.get("nowhere", 59))
        self.assertIsNone(cache.get("nowhere", 60))
        self.assertEqual(cache.stats()["unknown"], 0)


if __name__ == "__main__":
    unittest.main()
