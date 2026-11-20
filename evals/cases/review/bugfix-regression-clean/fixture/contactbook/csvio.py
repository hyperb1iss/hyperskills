"""CSV encoding of contacts."""

import csv

from .models import Contact

FIELDS = ("email", "name", "phone", "tags")
TAG_SEPARATOR = ";"


def write_contacts(contacts, fh, bom=False):
    """Write contacts as CSV to a text file object, header first.

    With ``bom``, the output starts with a UTF-8 byte-order mark. Spreadsheet apps
    decode a CSV with the system's legacy code page unless it starts with one.
    """
    if bom:
        fh.write("\ufeff")
    writer = csv.writer(fh, lineterminator="\r\n")
    writer.writerow(FIELDS)
    for contact in contacts:
        writer.writerow([contact.email, contact.name, contact.phone, TAG_SEPARATOR.join(contact.tags)])


def read_contacts(fh):
    """Read contacts written by write_contacts. Rows without an email are skipped."""
    contacts = []
    for row in csv.DictReader(fh):
        email = (row.get("email") or "").strip()
        if not email:
            continue
        tags = tuple(tag for tag in (row.get("tags") or "").split(TAG_SEPARATOR) if tag)
        contacts.append(
            Contact(email=email, name=row.get("name") or "", phone=row.get("phone") or "", tags=tags)
        )
    return contacts
