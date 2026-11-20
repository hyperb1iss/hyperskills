"""Users and the events we notify them about."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class User:
    """An account from the nightly export.

    ``utc_offset_minutes`` is the account's current offset from UTC, east positive.
    """

    id: str
    email: str
    name: str
    utc_offset_minutes: int = 0
    active: bool = True

    def tz(self):
        return timezone(timedelta(minutes=self.utc_offset_minutes))

    def local(self, moment):
        """``moment``, an aware datetime, in the user's local time."""
        return moment.astimezone(self.tz())


@dataclass(frozen=True)
class Event:
    id: str
    user_id: str
    kind: str
    subject: str
    occurred_at: datetime
    received_at: datetime
    url: str = ""
