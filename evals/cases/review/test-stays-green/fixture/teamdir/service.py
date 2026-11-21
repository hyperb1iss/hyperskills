"""Directory operations used by the HTTP handlers."""

from .cache import NullCache
from .store import ProfileNotFound


class DirectoryService:
    def __init__(self, store, cache=None):
        self._store = store
        self._cache = cache if cache is not None else NullCache()

    def get_profile(self, org_id, user_id):
        key = _profile_key(org_id, user_id)
        profile = self._cache.get(key)
        if profile is None:
            profile = self._store.load(org_id, user_id)
            self._cache.set(key, profile)
        return profile

    def update_profile(self, org_id, user_id, **changes):
        self._cache.delete(_profile_key(org_id, user_id))
        current = self.get_profile(org_id, user_id)
        updated = current.with_changes(**changes)
        self._store.save(updated)
        return updated

    def exists(self, org_id, user_id):
        try:
            self.get_profile(org_id, user_id)
        except ProfileNotFound:
            return False
        return True

    def list_org(self, org_id):
        return self._store.list_org(org_id)

    def search(self, org_id, query):
        needle = query.strip().lower()
        if not needle:
            return []
        return [
            profile
            for profile in self._store.list_org(org_id)
            if needle in profile.display_name.lower() or needle in profile.title.lower()
        ]


def _profile_key(org_id, user_id):
    return f"profile:{org_id}:{user_id}"
