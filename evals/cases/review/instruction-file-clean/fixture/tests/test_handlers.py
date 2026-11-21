import json
import unittest
from datetime import datetime, timezone

from docvault.models import Principal
from docvault.routes import Request, dispatch
from docvault.store import DocumentStore

WHEN = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)
ALL_SCOPES = frozenset({"docs:read", "docs:write", "docs:export"})
RIVER = Principal("u-1", "t-river", ALL_SCOPES)


def make_store():
    store = DocumentStore()
    store.add("t-river", "Runbook", "Restart the indexer.\n", "u-1", WHEN, tags=("ops",))
    store.add("t-river", "Draft", "Work in progress", "u-2", WHEN)
    store.add("t-stone", "Payroll", "Quarterly figures.", "u-9", WHEN)
    return store


def call(method, path, principal=RIVER, store=None, **kwargs):
    return dispatch(store or make_store(), principal, Request(method, path, **kwargs))


class DocumentTests(unittest.TestCase):
    def test_list_returns_own_tenant_only(self):
        status, body = call("GET", "/tenants/t-river/docs")
        self.assertEqual(status, 200)
        self.assertEqual(sorted(d["title"] for d in body["documents"]), ["Draft", "Runbook"])

    def test_get_document(self):
        status, body = call("GET", "/tenants/t-river/docs/doc_000001")
        self.assertEqual((status, body["body"]), (200, "Restart the indexer.\n"))

    def test_other_tenants_document_is_not_found(self):
        status, _ = call("GET", "/tenants/t-river/docs/doc_000003")
        self.assertEqual(status, 404)

    def test_path_tenant_must_match_caller(self):
        status, _ = call("GET", "/tenants/t-stone/docs")
        self.assertEqual(status, 403)

    def test_create_validates_title(self):
        status, _ = call("POST", "/tenants/t-river/docs", body={"title": "  "})
        self.assertEqual(status, 400)

    def test_create_then_archive(self):
        store = make_store()
        status, created = call("POST", "/tenants/t-river/docs", store=store, body={"title": "Notes", "tags": ["a"]})
        self.assertEqual(status, 201)
        status, archived = call("POST", f"/tenants/t-river/docs/{created['id']}/archive", store=store)
        self.assertTrue(archived["archived"])
        _, listing = call("GET", "/tenants/t-river/docs", store=store)
        self.assertNotIn(created["id"], [d["id"] for d in listing["documents"]])

    def test_write_requires_scope(self):
        reader = Principal("u-3", "t-river", frozenset({"docs:read"}))
        status, body = call("POST", "/tenants/t-river/docs", principal=reader, body={"title": "x"})
        self.assertEqual((status, body["scope"]), (403, "docs:write"))


class ExportTests(unittest.TestCase):
    def test_markdown_is_the_default(self):
        status, body = call("GET", "/tenants/t-river/docs/doc_000001/export")
        self.assertEqual(status, 200)
        self.assertEqual(body["filename"], "doc_000001.md")
        self.assertEqual(body["content"], "# Runbook\n\nTags: ops\n\nRestart the indexer.\n")

    def test_json_export(self):
        status, body = call("GET", "/tenants/t-river/docs/doc_000002/export", query={"format": "json"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body["content"])["title"], "Draft")

    def test_unknown_format(self):
        status, body = call("GET", "/tenants/t-river/docs/doc_000001/export", query={"format": "pdf"})
        self.assertEqual((status, body["supported"]), (400, ["json", "markdown"]))

    def test_export_requires_scope(self):
        reader = Principal("u-3", "t-river", frozenset({"docs:read"}))
        status, _ = call("GET", "/tenants/t-river/docs/doc_000001/export", principal=reader)
        self.assertEqual(status, 403)

    def test_export_under_another_tenant_is_forbidden(self):
        status, _ = call("GET", "/tenants/t-stone/docs/doc_000003/export")
        self.assertEqual(status, 403)

    def test_missing_document(self):
        status, _ = call("GET", "/tenants/t-river/docs/doc_999999/export")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
