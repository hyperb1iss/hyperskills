import unittest

from stockroom.settings import Settings, SettingsError


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        settings = Settings.from_env({})
        self.assertEqual((settings.low_stock_threshold, settings.max_adjustment), (5, 1000))

    def test_zero_threshold_is_kept(self):
        self.assertEqual(Settings.from_env({"STOCKROOM_LOW_STOCK_THRESHOLD": "0"}).low_stock_threshold, 0)

    def test_rejects_non_integer(self):
        with self.assertRaises(SettingsError):
            Settings.from_env({"STOCKROOM_MAX_ADJUSTMENT": "lots"})


if __name__ == "__main__":
    unittest.main()
