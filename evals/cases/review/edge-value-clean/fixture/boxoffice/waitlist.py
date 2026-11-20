"""First-come waitlist for a sold-out event."""
from collections import deque


class Waitlist:
    def __init__(self):
        self._buyers = deque()

    def __len__(self):
        return len(self._buyers)

    def join(self, buyer):
        if buyer not in self._buyers:
            self._buyers.append(buyer)
        return self._buyers.index(buyer) + 1

    def pop_next(self):
        return self._buyers.popleft()
