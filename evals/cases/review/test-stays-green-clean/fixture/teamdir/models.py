"""Profile records for the team directory."""

from dataclasses import dataclass, replace

EDITABLE_FIELDS = frozenset({"display_name", "title", "timezone", "pronouns"})
MAX_FIELD_LENGTH = 120


class InvalidChange(ValueError):
    """An update named a field that cannot be edited or gave a bad value."""


@dataclass(frozen=True)
class Profile:
    org_id: str
    user_id: str
    email: str
    display_name: str
    title: str = ""
    timezone: str = "UTC"
    pronouns: str = ""

    def with_changes(self, **changes):
        unknown = set(changes) - EDITABLE_FIELDS
        if unknown:
            raise InvalidChange("not editable: " + ", ".join(sorted(unknown)))
        for name, value in changes.items():
            if not isinstance(value, str):
                raise InvalidChange(f"{name} must be a string")
            if len(value) > MAX_FIELD_LENGTH:
                raise InvalidChange(f"{name} is longer than {MAX_FIELD_LENGTH} characters")
        if "display_name" in changes and not changes["display_name"].strip():
            raise InvalidChange("display_name cannot be blank")
        return replace(self, **changes)

    def label(self):
        if self.title:
            return f"{self.display_name} ({self.title})"
        return self.display_name
