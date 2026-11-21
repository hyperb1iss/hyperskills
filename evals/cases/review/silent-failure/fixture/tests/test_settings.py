import unittest

from courier.settings import RelaySettings


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        settings = RelaySettings.from_env({})
        self.assertEqual((settings.source, settings.poll_limit), ("orders", 500))

    def test_blank_values_use_defaults(self):
        self.assertEqual(RelaySettings.from_env({"COURIER_POLL_LIMIT": " "}).poll_limit, 500)

    def test_overrides(self):
        settings = RelaySettings.from_env({"COURIER_SOURCE": "billing", "COURIER_POLL_LIMIT": "50"})
        self.assertEqual((settings.source, settings.poll_limit), ("billing", 50))

    def test_rejects_non_numbers(self):
        with self.assertRaisesRegex(ValueError, "COURIER_POLL_LIMIT must be an integer"):
            RelaySettings.from_env({"COURIER_POLL_LIMIT": "fifty"})

    def test_rejects_zero(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            RelaySettings.from_env({"COURIER_POLL_LIMIT": "0"})


if __name__ == "__main__":
    unittest.main()
