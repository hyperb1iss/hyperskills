"""Proof for document export: a caller cannot export another tenant's document.

Run with the fixture root on sys.path. Fails on the defect fixture, passes on the clean one.
"""
import unittest
from datetime import datetime, timezone

from docvault.models import Principal
from docvault.routes import Request, dispatch
from docvault.store import DocumentStore


def make_store():
    store = DocumentStore()
    when = datetime(2026, 2, 1, tzinfo=timezone.utc)
    own = store.add("t-river", "Runbook", "Restart the indexer.", "u-1", when)
    other = store.add("t-stone", "Payroll", "Quarterly figures.", "u-9", when)
    return store, own, other


class ExportIsTenantScoped(unittest.TestCase):
    def test_other_tenants_document_is_not_exported(self):
        store, _, other = make_store()
        caller = Principal("u-1", "t-river", frozenset({"docs:read", "docs:export"}))
        status, body = dispatch(store, caller, Request("GET", f"/tenants/t-river/docs/{other.id}/export"))
        self.assertEqual(status, 404)
        self.assertNotIn("Quarterly figures.", str(body))

    def test_own_document_still_exports(self):
        store, own, _ = make_store()
        caller = Principal("u-1", "t-river", frozenset({"docs:export"}))
        status, body = dispatch(store, caller, Request("GET", f"/tenants/t-river/docs/{own.id}/export"))
        self.assertEqual(status, 200)
        self.assertIn("Restart the indexer.", body["content"])


if __name__ == "__main__":
    unittest.main()
