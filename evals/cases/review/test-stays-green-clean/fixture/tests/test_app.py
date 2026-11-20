import unittest

from teamdir.app import handle_get, handle_patch, handle_search
from teamdir.models import Profile
from teamdir.service import DirectoryService
from teamdir.store import ProfileStore


def make_service():
    return DirectoryService(ProfileStore([
        Profile("orchard", "u1", "ada@example.com", "Ada Park", title="Engineer"),
    ]))


class HandlerTests(unittest.TestCase):
    def test_get_returns_payload(self):
        status, body = handle_get(make_service(), "orchard", "u1")
        self.assertEqual(status, 200)
        self.assertEqual(body["name"], "Ada Park")

    def test_get_missing_is_404(self):
        status, _ = handle_get(make_service(), "orchard", "u9")
        self.assertEqual(status, 404)

    def test_patch_updates_title(self):
        status, body = handle_patch(make_service(), "orchard", "u1", {"title": "Lead"})
        self.assertEqual(status, 200)
        self.assertEqual(body["title"], "Lead")

    def test_patch_rejects_email_change(self):
        status, body = handle_patch(make_service(), "orchard", "u1", {"email": "x@example.com"})
        self.assertEqual(status, 400)
        self.assertIn("email", body["detail"])

    def test_patch_rejects_non_object_body(self):
        status, _ = handle_patch(make_service(), "orchard", "u1", ["title"])
        self.assertEqual(status, 400)

    def test_search(self):
        status, body = handle_search(make_service(), "orchard", "ada")
        self.assertEqual(status, 200)
        self.assertEqual([r["id"] for r in body["results"]], ["u1"])


if __name__ == "__main__":
    unittest.main()
