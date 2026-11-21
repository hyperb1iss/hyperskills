import os
import tempfile
import unittest

from contactbook.book import ContactBook
from contactbook.models import Contact
from contactbook.restore import restore_backup, restore_into

BACKUP = "email,name,phone,tags\r\nada@example.com,Ada Park,+15550100,vip\r\nben@example.com,Ben Ortiz,,\r\n"


class RestoreTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "backup.csv")
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            fh.write(BACKUP)

    def test_restore_backup(self):
        book = restore_backup(self.path)
        self.assertEqual(len(book), 2)
        self.assertEqual(book.find("ada@example.com").tags, ("vip",))

    def test_restore_into_keeps_existing_by_default(self):
        book = ContactBook([Contact("ada@example.com", "Ada P.")])
        self.assertEqual(restore_into(book, self.path), 1)
        self.assertEqual(book.find("ada@example.com").name, "Ada P.")

    def test_restore_into_can_overwrite(self):
        book = ContactBook([Contact("ada@example.com", "Ada P.")])
        self.assertEqual(restore_into(book, self.path, overwrite=True), 2)
        self.assertEqual(book.find("ada@example.com").name, "Ada Park")


if __name__ == "__main__":
    unittest.main()
