import io
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from digests import cadence
from digests.cli import Context, main
from digests.events import EventStore
from digests.job import DigestJob
from digests.ledger import DigestLedger
from digests.mailer import RecordingTransport
from digests.models import Event, User
from digests.preferences import PreferenceStore
from digests.settings import Settings
from digests.users import UserDirectory

MONDAY_0805 = datetime(2026, 3, 2, 8, 5, tzinfo=timezone.utc)


def always_due(prefs, local_now):
    return prefs.digest != "off"


def event(event_id, user_id, hours_before, kind="comment"):
    moment = MONDAY_0805 - timedelta(hours=hours_before)
    return Event(event_id, user_id, kind, f"{kind} {event_id}", moment, moment)


class DigestJobTests(unittest.TestCase):
    def setUp(self):
        self.users = UserDirectory([
            User("u-ada", "ada@example.com", "Ada Park"),
            User("u-ben", "ben@example.com", "Ben Ortiz", utc_offset_minutes=60),
            User("u-cy", "cy@example.com", "Cy Lund"),
        ])
        self.prefs = PreferenceStore([
            {"user_id": "u-ada", "digest": "daily", "digest_hour": 8},
            {"user_id": "u-ben", "digest": "daily", "digest_hour": 9},
            {"user_id": "u-cy", "digest": "weekly", "digest_hour": 8, "digest_weekday": 2},
        ])
        self.events = EventStore([event("e1", "u-ada", 2), event("e2", "u-ben", 3), event("e3", "u-cy", 30)])
        self.ledger = DigestLedger()
        self.transport = RecordingTransport()

    def make_job(self, **kwargs):
        kwargs.setdefault("is_due", always_due)
        return DigestJob(self.users, self.prefs, self.events, self.ledger, self.transport, Settings(), **kwargs)

    def test_sends_a_digest_to_each_due_user_with_events(self):
        report = self.make_job().run(MONDAY_0805)
        self.assertEqual(sorted(m.to for m in self.transport.sent), ["ada@example.com", "ben@example.com", "cy@example.com"])
        self.assertEqual(report.summary(), "due=3 empty=0 already_sent=0 sent=3 failed=0 invalid=0")

    def test_uses_each_users_local_hour(self):
        self.make_job(is_due=cadence.is_due).run(MONDAY_0805)
        self.assertEqual(sorted(m.to for m in self.transport.sent), ["ada@example.com", "ben@example.com"])

    def test_rerun_in_the_same_slot_sends_nothing(self):
        job = self.make_job()
        job.run(MONDAY_0805)
        report = job.run(MONDAY_0805 + timedelta(minutes=20))
        self.assertEqual((report.already_sent, len(self.transport.sent)), (3, 3))

    def test_next_digest_starts_where_the_last_one_ended(self):
        job = self.make_job()
        job.run(MONDAY_0805)
        self.events.add(event("e4", "u-ada", -2))
        self.transport.sent.clear()
        job.run(MONDAY_0805 + timedelta(days=1))
        ada = [m for m in self.transport.sent if m.to == "ada@example.com"]
        self.assertEqual(len(ada), 1)
        self.assertIn("comment e4", ada[0].body)
        self.assertNotIn("comment e1", ada[0].body)

    def test_user_with_nothing_new_gets_no_email_but_the_window_moves(self):
        self.events = EventStore()
        report = self.make_job().run(MONDAY_0805)
        self.assertEqual((report.empty, self.transport.sent), (3, []))
        self.assertEqual(self.ledger.cutoff_for("u-ada"), MONDAY_0805)

    def test_failed_first_digest_is_retried_over_the_same_window(self):
        self.transport = RecordingTransport(refuse={"ada@example.com"})
        report = self.make_job().run(MONDAY_0805)
        self.assertEqual(report.count("failed"), 1)
        self.assertEqual(self.ledger.cutoff_for("u-ada"), MONDAY_0805 - timedelta(days=1))
        self.assertEqual(self.ledger.cutoff_for("u-ben"), MONDAY_0805)
        self.transport = RecordingTransport()
        self.make_job().run(MONDAY_0805 + timedelta(days=1))
        ada = [m for m in self.transport.sent if m.to == "ada@example.com"]
        self.assertEqual(len(ada), 1)
        self.assertIn("comment e1", ada[0].body)

    def test_digest_command_dry_run_sends_and_records_nothing(self):
        context = Context(self.users, self.prefs, self.events, self.transport, Settings(), ledger=self.ledger)
        out = io.StringIO()
        code = main(["digest", "--now", MONDAY_0805.isoformat(), "--dry-run"], context, out)
        self.assertEqual(code, 0)
        self.assertIn("would send to ada@example.com: 1 update today", out.getvalue())
        self.assertEqual((self.transport.sent, self.ledger.cutoff_for("u-ada")), ([], None))

    def test_digest_command_refuses_now_on_a_real_run(self):
        context = Context(self.users, self.prefs, self.events, self.transport, Settings(), ledger=self.ledger)
        code = main(["digest", "--now", MONDAY_0805.isoformat()], context, io.StringIO())
        self.assertEqual((code, self.transport.sent, self.ledger.cutoff_for("u-ada")), (2, [], None))

    def test_weekly_digest_goes_out_on_the_chosen_day(self):
        wednesday = MONDAY_0805 + timedelta(days=2)
        self.make_job().run(wednesday)
        self.assertIn("cy@example.com", [m.to for m in self.transport.sent])


class LedgerTests(unittest.TestCase):
    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = DigestLedger(path)
            ledger.record("u-ada", MONDAY_0805)
            ledger.save()
            self.assertEqual(DigestLedger(path).cutoff_for("u-ada"), MONDAY_0805)
            self.assertEqual(os.listdir(tmp), ["ledger.json"])


if __name__ == "__main__":
    unittest.main()
