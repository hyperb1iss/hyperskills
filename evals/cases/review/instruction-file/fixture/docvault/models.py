"""Documents and the principals that act on them."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    scopes: frozenset = frozenset()

    def has_scope(self, scope):
        return scope in self.scopes


@dataclass
class Document:
    id: str
    tenant_id: str
    title: str
    body: str
    created_by: str
    created_at: datetime
    tags: tuple = ()
    archived: bool = False
