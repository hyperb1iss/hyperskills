"""Proof for the digest pull request: three independent properties.

Run with the fixture root on sys.path. All three fail on the defect fixture and
pass on the clean one.
"""
import unittest
from datetime import datetime, timedelta, timezone

from digests.cadence import is_due
from digests.events import EventStore
from digests.job import DigestJob
from digests.ledger import DigestLedger
from digests.mailer import Message, RecordingTransport
from digests.models import Event, User
from digests.preferences import PreferenceStore, Preferences
from digests.sender import send_batch
from digests.settings import Settings
from digests.users import UserDirectory

MONDAY_0805 = datetime(2026, 3, 2, 8, 5, tzinfo=timezone.utc)


def message(to):
    return Message(to=to, subject="1 update today", body="...", sender="digest@example.invalid", category="digest-daily")


class DigestProof(unittest.TestCase):
    def test_one_unusable_address_does_not_stop_the_batch(self):
        transport = RecordingTransport()
        batch = [("u-ada", message("ada@example.com")), ("u-ben", message("ben at example")), ("u-cy", message("cy@example.com"))]
        try:
            results = send_batch(transport, batch)
        except Exception as exc:
            self.fail(f"the batch stopped at an unusable address: {exc!r}")
        self.assertEqual([m.to for m in transport.sent], ["ada@example.com", "cy@example.com"])
        self.assertEqual([r.status for r in results], ["sent", "invalid", "sent"])

    def test_weekly_digest_is_due_on_the_chosen_weekday(self):
        monday_digest = Preferences("u-ada", digest="weekly", digest_hour=8, digest_weekday=0)
        self.assertTrue(is_due(monday_digest, MONDAY_0805))
        self.assertFalse(is_due(monday_digest, MONDAY_0805 + timedelta(days=1)))

    def test_event_stored_after_a_run_reaches_the_next_digest(self):
        users = UserDirectory([User("u-ada", "ada@example.com", "Ada Park")])
        prefs = PreferenceStore([{"user_id": "u-ada", "digest": "daily", "digest_hour": 8}])
        late = Event("late", "u-ada", "mention", "You were mentioned", MONDAY_0805 - timedelta(minutes=6),
                     MONDAY_0805 + timedelta(minutes=4))
        events = EventStore([Event("early", "u-ada", "comment", "New comment", MONDAY_0805 - timedelta(hours=3),
                                   MONDAY_0805 - timedelta(hours=3))])
        transport = RecordingTransport()
        job = DigestJob(users, prefs, events, DigestLedger(), transport, Settings())
        job.run(MONDAY_0805)
        events.add(late)
        job.run(MONDAY_0805 + timedelta(days=1))
        bodies = [m.body for m in transport.sent]
        self.assertEqual(len(bodies), 2)
        self.assertIn("You were mentioned", bodies[1])


if __name__ == "__main__":
    unittest.main()
