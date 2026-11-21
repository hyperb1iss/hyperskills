import unittest
from datetime import datetime, timedelta, timezone

from digests.collect import collect_digest
from digests.events import EventStore
from digests.models import Event, User
from digests.preferences import Preferences
from digests.render import render_digest
from digests.settings import Settings

SINCE = datetime(2026, 3, 1, 8, 5, tzinfo=timezone.utc)
UNTIL = SINCE + timedelta(days=1)
ADA = User("u-ada", "ada@example.com", "Ada Park")
DAILY = Preferences("u-ada", digest="daily")


def event(event_id, kind, hours, user_id="u-ada"):
    moment = SINCE + timedelta(hours=hours)
    return Event(event_id, user_id, kind, f"{kind} {event_id}", moment, moment, url=f"https://app.example.invalid/{event_id}")


class CollectTests(unittest.TestCase):
    def test_window_excludes_its_start_and_includes_its_end(self):
        store = EventStore([event("e0", "comment", 0), event("e1", "comment", 1), event("e2", "comment", 24)])
        digest = collect_digest(store, ADA, DAILY, SINCE, UNTIL, max_events=50)
        self.assertEqual([e.id for e in digest.sections[0].events], ["e2", "e1"])

    def test_sections_follow_the_fixed_order(self):
        store = EventStore([event("c", "comment", 1), event("r", "review_request", 2), event("m", "mention", 3)])
        digest = collect_digest(store, ADA, DAILY, SINCE, UNTIL, max_events=50)
        self.assertEqual([s.kind for s in digest.sections], ["review_request", "mention", "comment"])

    def test_muted_kinds_are_left_out(self):
        prefs = Preferences("u-ada", digest="daily", muted_kinds=frozenset({"follow"}))
        store = EventStore([event("f", "follow", 1), event("c", "comment", 2)])
        digest = collect_digest(store, ADA, prefs, SINCE, UNTIL, max_events=50)
        self.assertEqual([s.kind for s in digest.sections], ["comment"])

    def test_cap_applies_across_sections(self):
        store = EventStore([event(f"m{i}", "mention", i + 1) for i in range(3)] + [event("c", "comment", 5)])
        digest = collect_digest(store, ADA, DAILY, SINCE, UNTIL, max_events=2)
        mentions, comments = digest.sections
        self.assertEqual(([e.id for e in mentions.events], mentions.more), (["m2", "m1"], 1))
        self.assertEqual((comments.events, comments.more), ((), 1))
        self.assertEqual(digest.total, 4)


class RenderTests(unittest.TestCase):
    def setUp(self):
        store = EventStore([event(f"m{i}", "mention", i + 1) for i in range(3)])
        self.digest = collect_digest(store, ADA, DAILY, SINCE, UNTIL, max_events=2)

    def test_subject_and_body(self):
        message = render_digest(ADA, self.digest, "daily", Settings())
        self.assertEqual((message.subject, message.category), ("3 updates today", "digest-daily"))
        body = message.body
        self.assertIn("Mentions (3)\n- mention m2\n  https://app.example.invalid/m2\n", body)
        self.assertIn("- and 1 more\n", body)
        self.assertTrue(body.endswith(f"Change them at {Settings().preferences_url}\n"))


if __name__ == "__main__":
    unittest.main()
