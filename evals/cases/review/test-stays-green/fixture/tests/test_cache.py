import unittest

from teamdir.cache import NullCache, TTLCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TTLCacheTests(unittest.TestCase):
    def test_returns_value_before_expiry(self):
        clock = FakeClock()
        cache = TTLCache(ttl=10, clock=clock)
        cache.set("k", "v")
        clock.now = 9.5
        self.assertEqual(cache.get("k"), "v")
        self.assertEqual(cache.hits, 1)

    def test_expires_after_ttl(self):
        clock = FakeClock()
        cache = TTLCache(ttl=10, clock=clock)
        cache.set("k", "v")
        clock.now = 10
        self.assertIsNone(cache.get("k"))
        self.assertEqual(len(cache), 0)

    def test_delete_removes_entry(self):
        cache = TTLCache(ttl=10, clock=FakeClock())
        cache.set("k", "v")
        cache.delete("k")
        cache.delete("missing")
        self.assertIsNone(cache.get("k"))

    def test_evicts_soonest_expiring_when_full(self):
        clock = FakeClock()
        cache = TTLCache(ttl=10, clock=clock, max_entries=2)
        cache.set("a", 1)
        clock.now = 1
        cache.set("b", 2)
        cache.set("c", 3)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("c"), 3)

    def test_rejects_negative_ttl(self):
        with self.assertRaises(ValueError):
            TTLCache(ttl=-1)


class NullCacheTests(unittest.TestCase):
    def test_never_returns_a_value(self):
        cache = NullCache()
        cache.set("k", "v")
        self.assertIsNone(cache.get("k"))


if __name__ == "__main__":
    unittest.main()
