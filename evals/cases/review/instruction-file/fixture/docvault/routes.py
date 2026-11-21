"""Request routing. Requests are authenticated upstream; dispatch authorizes them."""

import re
from dataclasses import dataclass, field

from . import handlers
from .store import DocumentNotFound

TENANT = r"/tenants/(?P<tenant_id>[\w-]+)"
DOC = TENANT + r"/docs/(?P<doc_id>\w+)"


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)


ROUTES = [
    ("GET", TENANT + "/docs", handlers.list_documents, "docs:read"),
    ("POST", TENANT + "/docs", handlers.create_document, "docs:write"),
    ("GET", DOC, handlers.get_document, "docs:read"),
    ("POST", DOC + "/archive", handlers.archive_document, "docs:write"),
    ("GET", DOC + "/export", handlers.export_document, "docs:export"),
]


def dispatch(store, principal, request):
    """Authorize and route one request; returns ``(status, body)``."""
    for method, pattern, handler, scope in ROUTES:
        match = re.fullmatch(pattern, request.path)
        if match is None or method != request.method:
            continue
        params = match.groupdict()
        if params["tenant_id"] != principal.tenant_id:
            return 403, {"error": "forbidden"}
        if not principal.has_scope(scope):
            return 403, {"error": "missing_scope", "scope": scope}
        try:
            return handler(store, principal, request, **params)
        except DocumentNotFound:
            return 404, {"error": "not_found"}
    return 404, {"error": "no_route"}
