import unittest
from datetime import datetime, timedelta, timezone

from digests.cadence import is_due
from digests.preferences import Preferences

LOCAL = timezone(timedelta(hours=-5))
MORNING = datetime(2026, 3, 4, 8, 5, tzinfo=LOCAL)


class IsDueTests(unittest.TestCase):
    def test_off_is_never_due(self):
        self.assertFalse(is_due(Preferences("u-ada"), MORNING))

    def test_daily_is_due_during_the_chosen_local_hour(self):
        prefs = Preferences("u-ada", digest="daily", digest_hour=8)
        self.assertTrue(is_due(prefs, MORNING))
        self.assertTrue(is_due(prefs, MORNING.replace(minute=59)))
        self.assertFalse(is_due(prefs, MORNING + timedelta(hours=1)))
        self.assertFalse(is_due(prefs, MORNING - timedelta(hours=1)))



if __name__ == "__main__":
    unittest.main()
