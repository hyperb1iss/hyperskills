"""Geocoding client. Each planner worker keeps one client for the life of the process."""
import time

from .cache import NOT_FOUND, GeoCache
from .normalize import normalize


class GeocodeClient:
    def __init__(self, backend, cache=None, clock=time.monotonic):
        self.backend = backend
        self.cache = cache if cache is not None else GeoCache()
        self.clock = clock

    def lookup(self, address):
        """Return (lat, lon) for an address, or None when the backend cannot place it."""
        return self.lookup_many([address])[address]

    def lookup_many(self, addresses):
        """Resolve addresses, sending every cache miss to the backend in one batch call."""
        now = self.clock()
        keys = {address: normalize(address) for address in addresses}
        found, missing = {}, []
        for key in dict.fromkeys(keys.values()):
            cached = self.cache.get(key, now)
            if cached is None:
                missing.append(key)
            else:
                found[key] = None if cached is NOT_FOUND else cached
        if missing:
            results = self.backend.geocode_batch(missing)
            for key in missing:
                point = results.get(key)
                if point is None:
                    self.cache.put_unknown(key, now)
                else:
                    self.cache.put(key, point, now)
                found[key] = point
        return {address: found[key] for address, key in keys.items()}
