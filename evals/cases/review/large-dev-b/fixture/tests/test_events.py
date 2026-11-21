import unittest
from datetime import datetime, timedelta, timezone

from digests.events import EventStore
from digests.models import Event

T0 = datetime(2026, 3, 2, 8, 0, tzinfo=timezone.utc)


def event(event_id, occurred, received=None, user_id="u-ada", kind="comment"):
    return Event(event_id, user_id, kind, f"subject {event_id}", occurred, received or occurred)


class EventStoreTests(unittest.TestCase):
    def test_received_window_is_open_at_start(self):
        store = EventStore([event("e1", T0), event("e2", T0 + timedelta(minutes=5))])
        found = store.received_between("u-ada", T0, T0 + timedelta(minutes=5))
        self.assertEqual([e.id for e in found], ["e2"])

    def test_storage_order_follows_received_at(self):
        store = EventStore([
            event("late", T0 - timedelta(minutes=10), received=T0 + timedelta(minutes=2)),
            event("prompt", T0 + timedelta(minutes=1)),
        ])
        found = store.received_between("u-ada", T0 - timedelta(hours=1), T0 + timedelta(hours=1))
        self.assertEqual([e.id for e in found], ["prompt", "late"])

    def test_occurred_window_sorts_oldest_first(self):
        store = EventStore([
            event("b", T0 + timedelta(minutes=2)),
            event("a", T0 + timedelta(minutes=1), received=T0 + timedelta(minutes=3)),
        ])
        found = store.occurred_between("u-ada", T0, T0 + timedelta(minutes=10))
        self.assertEqual([e.id for e in found], ["a", "b"])

    def test_other_users_are_excluded(self):
        store = EventStore([event("e1", T0, user_id="u-ben")])
        self.assertEqual(store.received_between("u-ada", T0 - timedelta(hours=1), T0), [])

    def test_rejects_event_received_before_it_occurred(self):
        with self.assertRaises(ValueError):
            EventStore([event("bad", T0, received=T0 - timedelta(seconds=1))])


if __name__ == "__main__":
    unittest.main()
