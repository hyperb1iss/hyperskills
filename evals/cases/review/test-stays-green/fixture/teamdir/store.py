"""Profile storage.

Production backs this with the directory database; the interface is the same.
"""


class ProfileNotFound(LookupError):
    pass


class ProfileStore:
    def __init__(self, profiles=()):
        self._rows = {}
        for profile in profiles:
            self.save(profile)

    def load(self, org_id, user_id):
        try:
            return self._rows[(org_id, user_id)]
        except KeyError:
            raise ProfileNotFound(f"{org_id}/{user_id}") from None

    def save(self, profile):
        self._rows[(profile.org_id, profile.user_id)] = profile

    def list_org(self, org_id):
        return sorted(
            (profile for (org, _), profile in self._rows.items() if org == org_id),
            key=lambda profile: profile.display_name.lower(),
        )
