"""User directory, loaded from the nightly account export.

The export is JSON lines, one account per line. Accounts migrated from the legacy
system sometimes carry an email address the mailer cannot parse: a missing
domain, a stray space, or two addresses in one field. About 0.3 percent of active
accounts have one, and support corrects them as users report it.
"""

import json

from .models import User


class ExportError(ValueError):
    pass


class UserDirectory:
    def __init__(self, users=()):
        self._users = {user.id: user for user in users}

    @classmethod
    def from_export(cls, lines):
        users = []
        for number, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                users.append(User(
                    id=record["id"],
                    email=record.get("email") or "",
                    name=record.get("name") or "",
                    utc_offset_minutes=int(record.get("utc_offset_minutes", 0)),
                    active=bool(record.get("active", True)),
                ))
            except (ValueError, KeyError, TypeError) as exc:
                raise ExportError(f"line {number}: {exc}") from None
        return cls(users)

    def get(self, user_id):
        return self._users.get(user_id)

    def active(self):
        """Active accounts, ordered by id."""
        return sorted((user for user in self._users.values() if user.active), key=lambda user: user.id)

    def __len__(self):
        return len(self._users)
