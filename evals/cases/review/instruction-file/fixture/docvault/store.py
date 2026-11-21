"""Document storage."""

import itertools

from .models import Document


class DocumentNotFound(LookupError):
    pass


class DocumentStore:
    def __init__(self):
        self._docs = {}
        self._ids = itertools.count(1)

    def add(self, tenant_id, title, body, created_by, created_at, tags=()):
        doc_id = f"doc_{next(self._ids):06d}"
        doc = Document(doc_id, tenant_id, title, body, created_by, created_at, tuple(tags))
        self._docs[doc_id] = doc
        return doc

    def get(self, doc_id):
        """Fetch a document by id, whichever tenant owns it."""
        try:
            return self._docs[doc_id]
        except KeyError:
            raise DocumentNotFound(doc_id) from None

    def get_for_tenant(self, tenant_id, doc_id):
        """Fetch a document by id; another tenant's document counts as missing."""
        doc = self._docs.get(doc_id)
        if doc is None or doc.tenant_id != tenant_id:
            raise DocumentNotFound(doc_id)
        return doc

    def list_for_tenant(self, tenant_id, include_archived=False):
        docs = [doc for doc in self._docs.values() if doc.tenant_id == tenant_id]
        if not include_archived:
            docs = [doc for doc in docs if not doc.archived]
        return sorted(docs, key=lambda doc: (doc.created_at, doc.id), reverse=True)
