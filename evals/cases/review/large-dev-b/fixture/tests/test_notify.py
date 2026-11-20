import unittest
from datetime import datetime, timedelta, timezone

from digests.events import EventStore
from digests.mailer import RecordingTransport
from digests.models import Event, User
from digests.notify import notify_new_events
from digests.preferences import PreferenceStore
from digests.users import UserDirectory

T0 = datetime(2026, 3, 2, 8, 0, tzinfo=timezone.utc)
SENDER = "notify@example.invalid"


def event(event_id, user_id, kind="comment", minutes=1):
    moment = T0 + timedelta(minutes=minutes)
    return Event(event_id, user_id, kind, f"New {kind}", moment, moment, url=f"https://app.example.invalid/{event_id}")


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.users = UserDirectory([
            User("u-ada", "ada@example.com", "Ada Park"),
            User("u-ben", "ben at example", "Ben Ortiz"),
            User("u-cy", "cy@example.com", "Cy Lund"),
        ])
        self.prefs = PreferenceStore([{"user_id": "u-cy", "muted_kinds": ["follow"]}])
        self.store = EventStore([
            event("e1", "u-ada"), event("e2", "u-ben"), event("e3", "u-cy", kind="follow"), event("e4", "u-cy", minutes=2),
        ])

    def run_notify(self, transport):
        return notify_new_events(self.store, self.users, self.prefs, transport, T0, T0 + timedelta(minutes=5), SENDER)

    def test_sends_one_email_per_event_and_skips_bad_addresses(self):
        transport = RecordingTransport()
        report = self.run_notify(transport)
        self.assertEqual([m.to for m in transport.sent], ["ada@example.com", "cy@example.com"])
        self.assertEqual((report.sent, report.skipped), (2, 1))

    def test_muted_kinds_are_not_sent(self):
        transport = RecordingTransport()
        self.run_notify(transport)
        self.assertNotIn("New follow", [m.subject for m in transport.sent])

    def test_relay_failure_skips_only_that_message(self):
        transport = RecordingTransport(refuse={"ada@example.com"})
        report = self.run_notify(transport)
        self.assertEqual([m.to for m in transport.sent], ["cy@example.com"])
        self.assertEqual(report.skipped, 2)


if __name__ == "__main__":
    unittest.main()
