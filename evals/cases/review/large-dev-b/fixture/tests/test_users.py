import json
import unittest

from digests.users import ExportError, UserDirectory


def export(*records):
    return [json.dumps(record) for record in records]


class UserDirectoryTests(unittest.TestCase):
    def test_loads_export(self):
        users = UserDirectory.from_export(export(
            {"id": "u-ben", "email": "ben@example.com", "name": "Ben Ortiz", "utc_offset_minutes": -300},
            {"id": "u-ada", "email": "ada@example.com", "name": "Ada Park"},
        ))
        self.assertEqual([u.id for u in users.active()], ["u-ada", "u-ben"])
        self.assertEqual(users.get("u-ben").utc_offset_minutes, -300)

    def test_inactive_accounts_are_not_active(self):
        users = UserDirectory.from_export(export({"id": "u-cy", "email": "cy@example.com", "active": False}))
        self.assertEqual(users.active(), [])
        self.assertEqual(len(users), 1)

    def test_blank_lines_are_skipped(self):
        users = UserDirectory.from_export(["", json.dumps({"id": "u-ada"}), "  "])
        self.assertEqual(users.get("u-ada").email, "")

    def test_malformed_line_names_its_number(self):
        with self.assertRaises(ExportError) as caught:
            UserDirectory.from_export([json.dumps({"id": "u-ada"}), "{not json"])
        self.assertIn("line 2", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
