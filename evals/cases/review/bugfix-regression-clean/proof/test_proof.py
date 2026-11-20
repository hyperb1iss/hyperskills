"""Proof for the CSV fix: backups written by write_backup must still restore.

Run with the fixture root on sys.path. Fails on the defect fixture, passes on the clean one.
"""
import io
import os
import tempfile
import unittest

from contactbook.book import ContactBook
from contactbook.csvio import read_contacts, write_contacts
from contactbook.export import write_backup
from contactbook.models import Contact
from contactbook.restore import restore_backup, restore_into


def make_book():
    return ContactBook([
        Contact("ada@example.com", "Ada Park", "+15550100", ("vip",)),
        Contact("ben@example.com", "Ben Ortiz"),
    ])


class BackupRoundTrip(unittest.TestCase):
    def test_restore_returns_every_backed_up_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "contacts.csv")
            write_backup(make_book(), path)
            restored = restore_backup(path)
        self.assertEqual([c.email for c in restored.all()], ["ada@example.com", "ben@example.com"])
        self.assertEqual(restored.find("ada@example.com").tags, ("vip",))

    def test_restore_into_merges_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "contacts.csv")
            write_backup(make_book(), path)
            live = ContactBook()
            self.assertEqual(restore_into(live, path), 2)

    def test_writer_output_reads_back(self):
        out = io.StringIO()
        write_contacts(make_book().all(), out)
        self.assertEqual(len(read_contacts(io.StringIO(out.getvalue()))), 2)


if __name__ == "__main__":
    unittest.main()
