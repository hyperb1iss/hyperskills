"""Shared pieces for schema migrations."""


class MigrationError(Exception):
    """The stored rows cannot be upgraded as they are; nothing was changed."""
