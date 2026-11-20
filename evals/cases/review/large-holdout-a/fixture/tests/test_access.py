import unittest

from stockpile.access import (ADMIN, OPERATOR, VIEWER, Forbidden, Unauthorized, authenticate,
                              issue_key, require_role, revoke_key)
from stockpile.store import Store


class AuthenticateTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.key, self.token = issue_key(self.store, OPERATOR)

    def test_valid_token_returns_its_key(self):
        self.assertEqual(authenticate(self.store, "Bearer " + self.token), self.key)

    def test_secret_is_not_stored(self):
        row = self.store.key_row(self.key.key_id)
        self.assertNotIn(self.token.split(".", 1)[1], row.values())

    def test_wrong_secret_is_rejected(self):
        with self.assertRaises(Unauthorized):
            authenticate(self.store, f"Bearer {self.key.key_id}.not-the-secret")

    def test_revoked_key_is_rejected(self):
        revoke_key(self.store, self.key.key_id)
        with self.assertRaises(Unauthorized):
            authenticate(self.store, "Bearer " + self.token)

    def test_malformed_headers_are_rejected(self):
        for header in (None, "", "Basic abc", "Bearer ", "Bearer nodot", "Bearer .secret"):
            with self.subTest(header=header), self.assertRaises(Unauthorized):
                authenticate(self.store, header)

    def test_unknown_role_cannot_be_issued(self):
        with self.assertRaises(ValueError):
            issue_key(self.store, "superuser")


class RoleTest(unittest.TestCase):
    def test_roles_rank_viewer_operator_admin(self):
        store = Store()
        viewer, _ = issue_key(store, VIEWER)
        admin, _ = issue_key(store, ADMIN)
        require_role(viewer, "view")
        require_role(admin, "pick")
        with self.assertRaises(Forbidden):
            require_role(viewer, "reserve")


if __name__ == "__main__":
    unittest.main()
