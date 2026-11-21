import unittest

from digests.preferences import InvalidPreferences, PreferenceStore, Preferences


class PreferencesTests(unittest.TestCase):
    def test_defaults_for_users_without_a_record(self):
        prefs = PreferenceStore().get("u-ada")
        self.assertTrue(prefs.immediate)
        self.assertEqual(prefs.digest, "off")

    def test_muted_kinds_suppress_immediate_mail(self):
        prefs = Preferences.from_record({"user_id": "u-ada", "muted_kinds": ["follow"]})
        self.assertFalse(prefs.wants_immediate("follow"))
        self.assertTrue(prefs.wants_immediate("comment"))

    def test_unknown_muted_kind_is_rejected(self):
        with self.assertRaises(InvalidPreferences):
            Preferences.from_record({"user_id": "u-ada", "muted_kinds": ["gossip"]})

    def test_reads_digest_settings(self):
        prefs = Preferences.from_record({"user_id": "u-ada", "digest": "weekly", "digest_hour": "7", "digest_weekday": 4})
        self.assertEqual((prefs.digest, prefs.digest_hour, prefs.digest_weekday), ("weekly", 7, 4))

    def test_rejects_out_of_range_digest_settings(self):
        for record in (
            {"user_id": "u-ada", "digest": "hourly"},
            {"user_id": "u-ada", "digest_hour": 24},
            {"user_id": "u-ada", "digest_weekday": 7},
            {"user_id": "u-ada", "digest_hour": "noon"},
        ):
            with self.subTest(record=record), self.assertRaises(InvalidPreferences):
                Preferences.from_record(record)


if __name__ == "__main__":
    unittest.main()
