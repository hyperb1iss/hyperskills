"""In-memory contact book keyed by normalized email."""

from .models import normalize_email


class DuplicateContact(ValueError):
    pass


class ContactBook:
    def __init__(self, contacts=()):
        self._by_email = {}
        for contact in contacts:
            self.add(contact)

    def add(self, contact, replace=False):
        if contact.email in self._by_email and not replace:
            raise DuplicateContact(contact.email)
        self._by_email[contact.email] = contact

    def find(self, email):
        return self._by_email.get(normalize_email(email))

    def remove(self, email):
        return self._by_email.pop(normalize_email(email), None) is not None

    def all(self):
        return sorted(self._by_email.values(), key=lambda c: (c.name.lower(), c.email))

    def tagged(self, tag):
        return [contact for contact in self.all() if tag in contact.tags]

    def __len__(self):
        return len(self._by_email)
