import io
import unittest
from datetime import datetime, timedelta, timezone

from digests.cli import Context, main
from digests.events import EventStore
from digests.mailer import RecordingTransport
from digests.models import Event, User
from digests.preferences import PreferenceStore
from digests.settings import Settings
from digests.users import UserDirectory

T0 = datetime(2026, 3, 2, 8, 0, tzinfo=timezone.utc)


def make_context(transport):
    moment = T0 + timedelta(minutes=1)
    return Context(
        users=UserDirectory([User("u-ada", "ada@example.com", "Ada Park")]),
        prefs=PreferenceStore(),
        events=EventStore([Event("e1", "u-ada", "comment", "New comment", moment, moment)]),
        transport=transport,
        settings=Settings(),
        clock=lambda: T0 + timedelta(minutes=5),
    )


class NotifyCommandTests(unittest.TestCase):
    def test_notify_sends_and_reports(self):
        transport, out = RecordingTransport(), io.StringIO()
        code = main(["notify", "--since", T0.isoformat()], make_context(transport), out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "sent=1 skipped=0")

    def test_until_must_follow_since(self):
        out = io.StringIO()
        code = main(["notify", "--since", T0.isoformat(), "--until", T0.isoformat()], make_context(RecordingTransport()), out)
        self.assertEqual(code, 2)

    def test_timestamps_need_an_offset(self):
        with self.assertRaises(SystemExit):
            main(["notify", "--since", "2026-03-02T08:00:00"], make_context(RecordingTransport()), io.StringIO())


if __name__ == "__main__":
    unittest.main()
