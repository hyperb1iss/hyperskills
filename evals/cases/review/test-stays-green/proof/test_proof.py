"""Proof for the profile cache: an update must be visible to the next read.

Run with the fixture root on sys.path. Fails on the defect fixture, passes on the clean one.
"""
import unittest

from teamdir.cache import TTLCache
from teamdir.models import Profile
from teamdir.service import DirectoryService
from teamdir.store import ProfileStore


class FrozenClock:
    def __call__(self):
        return 500.0


def make_service():
    store = ProfileStore([Profile("orchard", "u1", "ada@example.com", "Ada Park", title="Engineer")])
    return DirectoryService(store, cache=TTLCache(ttl=300, clock=FrozenClock()))


class UpdateIsVisibleThroughCache(unittest.TestCase):
    def test_read_after_update_returns_new_values(self):
        service = make_service()
        service.get_profile("orchard", "u1")
        service.update_profile("orchard", "u1", title="Staff Engineer")
        self.assertEqual(service.get_profile("orchard", "u1").title, "Staff Engineer")

    def test_update_of_uncached_profile_is_visible(self):
        service = make_service()
        service.update_profile("orchard", "u1", title="Staff Engineer")
        self.assertEqual(service.get_profile("orchard", "u1").title, "Staff Engineer")


if __name__ == "__main__":
    unittest.main()
