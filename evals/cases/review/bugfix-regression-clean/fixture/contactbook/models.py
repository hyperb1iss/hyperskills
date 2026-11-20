"""Contact records."""

from dataclasses import dataclass


def normalize_email(email):
    return email.strip().lower()


@dataclass(frozen=True)
class Contact:
    email: str
    name: str = ""
    phone: str = ""
    tags: tuple = ()

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"invalid email {self.email!r}")
        object.__setattr__(self, "email", normalize_email(self.email))
        object.__setattr__(self, "tags", tuple(self.tags))
