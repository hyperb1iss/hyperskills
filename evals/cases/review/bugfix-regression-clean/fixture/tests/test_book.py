import unittest

from contactbook.book import ContactBook, DuplicateContact
from contactbook.models import Contact


class ContactBookTests(unittest.TestCase):
    def test_emails_are_normalized(self):
        book = ContactBook([Contact(" Ada@Example.com ", "Ada Park")])
        self.assertEqual(book.find("ADA@example.com").name, "Ada Park")

    def test_duplicate_rejected_unless_replacing(self):
        book = ContactBook([Contact("ada@example.com", "Ada")])
        with self.assertRaises(DuplicateContact):
            book.add(Contact("ada@example.com", "Ada Park"))
        book.add(Contact("ada@example.com", "Ada Park"), replace=True)
        self.assertEqual(book.find("ada@example.com").name, "Ada Park")

    def test_all_sorted_by_name(self):
        book = ContactBook([Contact("b@example.com", "Ben"), Contact("a@example.com", "ada")])
        self.assertEqual([c.email for c in book.all()], ["a@example.com", "b@example.com"])

    def test_tagged_and_remove(self):
        book = ContactBook([Contact("a@example.com", "Ada", tags=["vip"]), Contact("b@example.com", "Ben")])
        self.assertEqual([c.email for c in book.tagged("vip")], ["a@example.com"])
        self.assertTrue(book.remove("A@example.com"))
        self.assertEqual(len(book), 1)

    def test_invalid_email(self):
        with self.assertRaises(ValueError):
            Contact("not-an-email")


if __name__ == "__main__":
    unittest.main()
