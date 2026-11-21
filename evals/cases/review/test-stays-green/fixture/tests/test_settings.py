import unittest

from teamdir.app import build_service
from teamdir.cache import NullCache
from teamdir.settings import Settings, SettingsError


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        settings = Settings.from_env({})
        self.assertEqual(settings.listen_port, 8080)
        self.assertEqual(settings.profile_cache_ttl, 300)

    def test_reads_environment(self):
        settings = Settings.from_env({"TEAMDIR_PAGE_SIZE": "20", "TEAMDIR_PROFILE_CACHE_TTL": "0"})
        self.assertEqual(settings.page_size, 20)
        self.assertEqual(settings.profile_cache_ttl, 0)

    def test_rejects_non_integer(self):
        with self.assertRaises(SettingsError):
            Settings.from_env({"TEAMDIR_PORT": "eighty"})

    def test_rejects_port_zero(self):
        with self.assertRaises(SettingsError):
            Settings.from_env({"TEAMDIR_PORT": "0"})


class BuildServiceTests(unittest.TestCase):
    def test_zero_ttl_disables_cache(self):
        service = build_service(settings=Settings(profile_cache_ttl=0))
        self.assertIsInstance(service._cache, NullCache)


if __name__ == "__main__":
    unittest.main()
