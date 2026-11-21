"""Document service: storage, routing, handlers, and export formats."""

from .models import Document, Principal
from .routes import Request, dispatch
from .store import DocumentStore

__all__ = ["Document", "DocumentStore", "Principal", "Request", "dispatch"]
