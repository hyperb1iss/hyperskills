import codecs
import os
import tempfile
import unittest
from datetime import date

from contactbook.book import ContactBook
from contactbook.export import download_response, write_backup
from contactbook.models import Contact

TODAY = date(2026, 3, 2)


def make_book():
    return ContactBook([
        Contact("ada@example.com", "Ada Park", "+15550100", ("vip",)),
        Contact("ben@example.com", "Ben Ortiz"),
    ])


class DownloadTests(unittest.TestCase):
    def test_filename_and_headers(self):
        download = download_response(make_book(), TODAY)
        self.assertEqual(download.filename, "contacts-2026-03-02.csv")
        headers = download.headers()
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(headers["Content-Disposition"], 'attachment; filename="contacts-2026-03-02.csv"')
        self.assertEqual(headers["Content-Length"], str(len(download.body)))

    def test_body_lists_contacts(self):
        text = download_response(make_book(), TODAY).body.decode("utf-8")
        self.assertIn("ada@example.com,Ada Park,+15550100,vip", text)

    def test_starts_with_utf8_byte_order_mark(self):
        body = download_response(make_book(), TODAY).body
        self.assertTrue(body.startswith(codecs.BOM_UTF8))

    def test_accented_name_decodes_intact(self):
        book = make_book()
        book.add(Contact("zoe@example.com", "Zo\u00eb Brandt"))
        text = download_response(book, TODAY).body.decode("utf-8-sig")
        self.assertIn("zoe@example.com,Zo\u00eb Brandt", text)
        self.assertTrue(text.startswith("email,name,phone,tags"))


class BackupTests(unittest.TestCase):
    def test_backup_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "contacts.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("stale")
            write_backup(make_book(), path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertEqual(os.listdir(tmp), ["contacts.csv"])
        self.assertIn("ben@example.com,Ben Ortiz", content)
        self.assertNotIn("stale", content)


if __name__ == "__main__":
    unittest.main()
