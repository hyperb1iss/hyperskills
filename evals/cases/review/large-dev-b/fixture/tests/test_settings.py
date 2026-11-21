import unittest

from digests.settings import Settings, SettingsError


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        settings = Settings.from_env({})
        self.assertEqual(settings.sender, "Notifications <notify@example.invalid>")

    def test_reads_environment(self):
        settings = Settings.from_env({"NOTIFY_SENDER": "Ops <ops@example.invalid>"})
        self.assertEqual(settings.sender, "Ops <ops@example.invalid>")

    def test_rejects_bad_integers(self):
        with self.assertRaises(SettingsError):
            Settings.from_env({"NOTIFY_RELAY_TIMEOUT": "soon"})


if __name__ == "__main__":
    unittest.main()
