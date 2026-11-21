import unittest
from datetime import datetime, timedelta, timezone

from stockroom import api
from stockroom.events import EventLog, export_rows
from stockroom.models import Event, Principal
from stockroom.settings import Settings

from tests.helpers import make_stock

T0 = datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc)


class EventLogTests(unittest.TestCase):
    def test_since_is_exclusive(self):
        log = EventLog()
        log.record(Event(T0, "adjust", "TEA-01", "east", 1))
        log.record(Event(T0 + timedelta(seconds=5), "pick", "TEA-01", "east", -1))
        self.assertEqual([e.kind for e in log.since(T0)], ["pick"])
        self.assertEqual(len(log.of_kind("adjust")), 1)

    def test_export_rows_are_oldest_first(self):
        later = Event(T0 + timedelta(minutes=1), "pick", "TEA-01", "east", -2, "E-01x2")
        earlier = Event(T0, "receive", "TEA-01", "east", 5, "E-01")
        self.assertEqual(export_rows([later, earlier])[0], ("2026-04-06T09:00:00+00:00", "receive", "TEA-01",
                                                            "east", 5, "E-01"))


class EventsHandlerTests(unittest.TestCase):
    def setUp(self):
        stock, self.clock = make_stock()
        self.ctx = api.Context(stock, Settings())
        stock.adjust("TEA-01", "east", None, -1, "damaged")

    def test_admin_export(self):
        admin = Principal("k-admin", frozenset({"admin"}))
        status, body = api.get_events(self.ctx, admin, {"since": "2026-04-06T08:00:00+00:00"})
        self.assertEqual((status, len(body["rows"]), body["fields"][0]), (200, 1, "at"))

    def test_rejects_naive_or_missing_since(self):
        admin = Principal("k-admin", frozenset({"admin"}))
        self.assertEqual(api.get_events(self.ctx, admin, {"since": "2026-04-06T08:00:00"})[0], 400)
        self.assertEqual(api.get_events(self.ctx, admin, {})[0], 400)

    def test_non_admin_is_forbidden(self):
        clerk = Principal("k-clerk", frozenset({"stock:read"}), frozenset({"east"}))
        self.assertEqual(api.get_events(self.ctx, clerk, {"since": "2026-04-06T08:00:00+00:00"})[0], 403)


if __name__ == "__main__":
    unittest.main()
