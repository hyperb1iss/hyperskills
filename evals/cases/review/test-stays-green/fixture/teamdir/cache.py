"""In-process caches for read-heavy lookups."""

import time


class TTLCache:
    """Keeps each value for ``ttl`` seconds after it is stored.

    Not thread-safe; the directory API serves requests from one thread.
    """

    def __init__(self, ttl, clock=time.monotonic, max_entries=10_000):
        if ttl < 0:
            raise ValueError("ttl must be non-negative")
        self._ttl = ttl
        self._clock = clock
        self._max_entries = max_entries
        self._entries = {}
        self.hits = 0
        self.misses = 0

    def get(self, key):
        entry = self._entries.get(key)
        if entry is not None and self._clock() >= entry[1]:
            del self._entries[key]
            entry = None
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        return entry[0]

    def set(self, key, value):
        if key not in self._entries and len(self._entries) >= self._max_entries:
            soonest = min(self._entries, key=lambda k: self._entries[k][1])
            del self._entries[soonest]
        self._entries[key] = (value, self._clock() + self._ttl)

    def delete(self, key):
        self._entries.pop(key, None)

    def __len__(self):
        return len(self._entries)


class NullCache:
    """Cache interface that stores nothing."""

    def get(self, key):
        return None

    def set(self, key, value):
        pass

    def delete(self, key):
        pass
