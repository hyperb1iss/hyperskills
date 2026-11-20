"""Bounded LRU cache for geocoding results."""
from collections import OrderedDict

NOT_FOUND = object()


class GeoCache:
    def __init__(self, max_entries=10_000, ttl=86_400, unknown_ttl=3_600):
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self.max_entries = max_entries
        self.ttl = ttl
        self.unknown_ttl = unknown_ttl
        self._entries = OrderedDict()
        self._unknown = {}
        self.hits = 0
        self.misses = 0

    def get(self, key, now):
        expires = self._unknown.get(key)
        if expires is not None:
            if expires > now:
                self.hits += 1
                return NOT_FOUND
            del self._unknown[key]
        item = self._entries.get(key)
        if item is None or item[1] <= now:
            self._entries.pop(key, None)
            self.misses += 1
            return None
        self._entries.move_to_end(key)
        self.hits += 1
        return item[0]

    def put(self, key, point, now):
        self._entries[key] = (point, now + self.ttl)
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def put_unknown(self, key, now):
        """Remember that the backend could not place key, so repeats skip the backend."""
        self._unknown.pop(key, None)
        self._unknown[key] = now + self.unknown_ttl
        while len(self._unknown) > self.max_entries:
            del self._unknown[next(iter(self._unknown))]

    def stats(self):
        return {"entries": len(self._entries), "unknown": len(self._unknown), "hits": self.hits, "misses": self.misses}

    def __len__(self):
        return len(self._entries)
