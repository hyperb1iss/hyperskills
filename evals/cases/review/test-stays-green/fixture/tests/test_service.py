import unittest

from teamdir.cache import TTLCache
from teamdir.models import InvalidChange, Profile
from teamdir.service import DirectoryService
from teamdir.store import ProfileNotFound, ProfileStore


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


class CountingStore(ProfileStore):
    def __init__(self, profiles=()):
        super().__init__(profiles)
        self.loads = 0

    def load(self, org_id, user_id):
        self.loads += 1
        return super().load(org_id, user_id)


def make_service(**kwargs):
    store = CountingStore([
        Profile("orchard", "u1", "ada@example.com", "Ada Park", title="Engineer"),
        Profile("orchard", "u2", "ben@example.com", "Ben Ortiz", title="Designer"),
        Profile("harbor", "u1", "cy@example.com", "Cy Lund"),
    ])
    return DirectoryService(store, **kwargs), store


class GetProfileTests(unittest.TestCase):
    def test_returns_stored_profile(self):
        service, _ = make_service()
        self.assertEqual(service.get_profile("orchard", "u1").display_name, "Ada Park")

    def test_profiles_are_scoped_by_org(self):
        service, _ = make_service()
        self.assertEqual(service.get_profile("harbor", "u1").display_name, "Cy Lund")

    def test_missing_profile_raises(self):
        service, _ = make_service()
        with self.assertRaises(ProfileNotFound):
            service.get_profile("orchard", "nobody")

    def test_repeat_reads_are_served_from_cache(self):
        service, store = make_service(cache=TTLCache(ttl=60, clock=FakeClock()))
        service.get_profile("orchard", "u1")
        service.get_profile("orchard", "u1")
        self.assertEqual(store.loads, 1)


class UpdateProfileTests(unittest.TestCase):
    def test_update_returns_changed_profile(self):
        service, _ = make_service()
        updated = service.update_profile("orchard", "u1", title="Staff Engineer")
        self.assertEqual(updated.title, "Staff Engineer")
        self.assertEqual(updated.email, "ada@example.com")

    def test_update_invalidates_cached_profile(self):
        service, _ = make_service()
        service.get_profile("orchard", "u1")
        service.update_profile("orchard", "u1", title="Staff Engineer")
        self.assertEqual(service.get_profile("orchard", "u1").title, "Staff Engineer")

    def test_update_rejects_uneditable_field(self):
        service, _ = make_service()
        with self.assertRaises(InvalidChange):
            service.update_profile("orchard", "u1", email="other@example.com")

    def test_update_rejects_blank_name(self):
        service, _ = make_service()
        with self.assertRaises(InvalidChange):
            service.update_profile("orchard", "u1", display_name="  ")


class SearchTests(unittest.TestCase):
    def test_matches_name_or_title(self):
        service, _ = make_service()
        names = [p.display_name for p in service.search("orchard", "design")]
        self.assertEqual(names, ["Ben Ortiz"])

    def test_blank_query_returns_nothing(self):
        service, _ = make_service()
        self.assertEqual(service.search("orchard", "   "), [])


if __name__ == "__main__":
    unittest.main()
