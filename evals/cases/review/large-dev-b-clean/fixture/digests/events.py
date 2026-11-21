"""Event storage.

Producers stamp each event with ``occurred_at``, the time it happened on their
side. The ingest queue stamps ``received_at`` when it stores the event. Ingest
usually lags by a few seconds, but during producer backfills and queue failovers
the lag reaches 15 minutes, so an event can be stored well after the time it
occurred. Storage order follows ``received_at``.
"""

import bisect


class EventStore:
    def __init__(self, events=()):
        self._events = []
        self._keys = []
        for event in events:
            self.add(event)

    def add(self, event):
        if event.received_at < event.occurred_at:
            raise ValueError(f"event {event.id} was received before it occurred")
        index = bisect.bisect_right(self._keys, event.received_at)
        self._keys.insert(index, event.received_at)
        self._events.insert(index, event)

    def received_between(self, user_id, start, end):
        """Events for ``user_id`` stored in the window (start, end], in storage order."""
        return [
            event for event in self._events
            if event.user_id == user_id and start < event.received_at <= end
        ]

    def occurred_between(self, user_id, start, end):
        """Events for ``user_id`` that happened in the window (start, end], oldest first.

        For activity views that show what happened during a period.
        """
        found = [
            event for event in self._events
            if event.user_id == user_id and start < event.occurred_at <= end
        ]
        return sorted(found, key=lambda event: (event.occurred_at, event.id))

    def __len__(self):
        return len(self._events)
