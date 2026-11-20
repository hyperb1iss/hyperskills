"""Restore contacts from a backup file written by export.write_backup."""

from .book import ContactBook
from .csvio import read_contacts


def restore_backup(path):
    with open(path, encoding="utf-8", newline="") as fh:
        contacts = read_contacts(fh)
    return ContactBook(contacts)


def restore_into(book, path, overwrite=False):
    """Merge a backup into ``book``. Returns how many contacts were added or replaced."""
    changed = 0
    for contact in restore_backup(path).all():
        if overwrite or book.find(contact.email) is None:
            book.add(contact, replace=True)
            changed += 1
    return changed
