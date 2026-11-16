"""In-memory request limiting helpers."""


class RateWindow:
    """Counts events per key inside a sliding window of `seconds`."""

    def __init__(self, seconds):
        self.seconds = seconds
        self._events = {}

    def hit(self, key, now):
        """Record an event and return how many the key has inside the window."""
        cutoff = now - self.seconds
        for other in [k for k, times in self._events.items() if times[-1] <= cutoff]:
            del self._events[other]
        times = [t for t in self._events.get(key, []) if t > cutoff]
        times.append(now)
        self._events[key] = times
        return len(times)


class SeenTokens:
    """Remembers one-time tokens for `ttl` seconds so a replay can be rejected."""

    def __init__(self, ttl):
        self.ttl = ttl
        self._tokens = {}

    def seen(self, token, now):
        """Return True if the token was already presented within the last ttl seconds, and remember it."""
        cutoff = now - self.ttl
        for other in [t for t, at in self._tokens.items() if at <= cutoff]:
            del self._tokens[other]
        known = token in self._tokens
        self._tokens[token] = now
        return known
