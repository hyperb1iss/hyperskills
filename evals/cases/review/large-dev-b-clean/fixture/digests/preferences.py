"""Per-user notification preferences.

Stored as one record per user in the preferences table. A user with no record
gets the defaults. The settings API validates every record before storing it,
so the table holds only valid records; loading treats an invalid one as
corruption and raises.
"""

from dataclasses import dataclass

KNOWN_KINDS = frozenset({"comment", "mention", "follow", "review_request", "release"})
DIGEST_CADENCES = ("off", "daily", "weekly")


class InvalidPreferences(ValueError):
    pass


@dataclass(frozen=True)
class Preferences:
    """One user's settings.

    ``digest`` is "off", "daily", or "weekly". ``digest_hour`` is the local hour,
    0 to 23, in which the digest goes out. ``digest_weekday`` picks the day of a
    weekly digest, 0 for Monday through 6 for Sunday, as in ``datetime.weekday()``.
    """

    user_id: str
    immediate: bool = True
    muted_kinds: frozenset = frozenset()
    digest: str = "off"
    digest_hour: int = 8
    digest_weekday: int = 0

    def __post_init__(self):
        if self.digest not in DIGEST_CADENCES:
            raise InvalidPreferences(f"digest must be one of {', '.join(DIGEST_CADENCES)}")
        if not 0 <= self.digest_hour <= 23:
            raise InvalidPreferences("digest_hour must be 0 to 23")
        if not 0 <= self.digest_weekday <= 6:
            raise InvalidPreferences("digest_weekday must be 0 to 6")

    def wants_immediate(self, kind):
        return self.immediate and kind not in self.muted_kinds

    def wants_in_digest(self, kind):
        return self.digest != "off" and kind not in self.muted_kinds

    @classmethod
    def from_record(cls, record):
        muted = frozenset(record.get("muted_kinds", ()))
        unknown = muted - KNOWN_KINDS
        if unknown:
            raise InvalidPreferences("unknown kinds: " + ", ".join(sorted(unknown)))
        try:
            return cls(
                user_id=record["user_id"],
                immediate=bool(record.get("immediate", True)),
                muted_kinds=muted,
                digest=record.get("digest", "off"),
                digest_hour=int(record.get("digest_hour", 8)),
                digest_weekday=int(record.get("digest_weekday", 0)),
            )
        except InvalidPreferences:
            raise
        except (TypeError, ValueError) as exc:
            raise InvalidPreferences(str(exc)) from None


class PreferenceStore:
    def __init__(self, records=()):
        self._prefs = {}
        for record in records:
            prefs = Preferences.from_record(record)
            self._prefs[prefs.user_id] = prefs

    def get(self, user_id):
        return self._prefs.get(user_id) or Preferences(user_id)

    def set(self, prefs):
        self._prefs[prefs.user_id] = prefs
