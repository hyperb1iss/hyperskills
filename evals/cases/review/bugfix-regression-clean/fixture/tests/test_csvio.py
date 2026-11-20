import io
import unittest

from contactbook.csvio import read_contacts, write_contacts
from contactbook.models import Contact


class WriteTests(unittest.TestCase):
    def test_rows_and_quoting(self):
        out = io.StringIO()
        write_contacts([Contact("ada@example.com", "Park, Ada", "+15550100", ("vip", "board"))], out)
        self.assertIn('ada@example.com,"Park, Ada",+15550100,vip;board\r\n', out.getvalue())

    def test_byte_order_mark_flag(self):
        marked, plain = io.StringIO(), io.StringIO()
        write_contacts([], marked, bom=True)
        write_contacts([], plain, bom=False)
        self.assertEqual(marked.getvalue(), "\ufeffemail,name,phone,tags\r\n")
        self.assertEqual(plain.getvalue(), "email,name,phone,tags\r\n")


class ReadTests(unittest.TestCase):
    def test_parses_tags_and_skips_rows_without_email(self):
        text = "email,name,phone,tags\r\nben@example.com,Ben Ortiz,,ops;oncall\r\n,No Email,,\r\n"
        contacts = read_contacts(io.StringIO(text))
        self.assertEqual([(c.email, c.tags) for c in contacts], [("ben@example.com", ("ops", "oncall"))])

    def test_missing_columns_default_to_empty(self):
        contacts = read_contacts(io.StringIO("email\r\ncy@example.com\r\n"))
        self.assertEqual((contacts[0].name, contacts[0].phone, contacts[0].tags), ("", "", ()))


if __name__ == "__main__":
    unittest.main()
