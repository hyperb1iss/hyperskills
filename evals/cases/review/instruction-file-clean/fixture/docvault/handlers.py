"""Request handlers. Each returns ``(status, body)``."""

from datetime import datetime, timezone

from .exporters import FORMATS

MAX_TITLE_LENGTH = 200
MAX_TAGS = 20


def _summary(doc):
    return {"id": doc.id, "title": doc.title, "tags": list(doc.tags), "archived": doc.archived}


def list_documents(store, principal, request, tenant_id):
    include_archived = request.query.get("archived") == "1"
    docs = store.list_for_tenant(tenant_id, include_archived=include_archived)
    return 200, {"documents": [_summary(doc) for doc in docs]}


def get_document(store, principal, request, tenant_id, doc_id):
    doc = store.get_for_tenant(tenant_id, doc_id)
    return 200, dict(_summary(doc), body=doc.body, created_by=doc.created_by)


def create_document(store, principal, request, tenant_id):
    title = request.body.get("title")
    if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE_LENGTH:
        return 400, {"error": "invalid_title"}
    body = request.body.get("body", "")
    tags = request.body.get("tags", [])
    if not isinstance(body, str):
        return 400, {"error": "invalid_body"}
    if not isinstance(tags, list) or len(tags) > MAX_TAGS or not all(isinstance(t, str) for t in tags):
        return 400, {"error": "invalid_tags"}
    doc = store.add(tenant_id, title.strip(), body, principal.user_id, datetime.now(timezone.utc), tags)
    return 201, _summary(doc)


def archive_document(store, principal, request, tenant_id, doc_id):
    doc = store.get_for_tenant(tenant_id, doc_id)
    doc.archived = True
    return 200, _summary(doc)


def export_document(store, principal, request, tenant_id, doc_id):
    name = request.query.get("format", "markdown")
    fmt = FORMATS.get(name)
    if fmt is None:
        return 400, {"error": "unknown_format", "supported": sorted(FORMATS)}
    doc = store.get_for_tenant(tenant_id, doc_id)
    return 200, {
        "filename": f"{doc.id}.{fmt.extension}",
        "content_type": fmt.content_type,
        "content": fmt.render(doc),
    }
