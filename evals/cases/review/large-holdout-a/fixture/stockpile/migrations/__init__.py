"""Schema migrations for the store.

A migration module exposes VERSION and upgrade(store, now). migrate() runs
every migration newer than store.schema_version, in VERSION order and once
each, while holding the store lock, and records the new version after each one
succeeds. upgrade must leave store.tables untouched when it raises: it builds
replacement rows first and swaps them in at the end. Running migrate() on an
up-to-date store does nothing.
"""
from . import m0002_bin_codes, m0003_key_roles, m0004_holds_and_scopes
from .common import MigrationError

MIGRATIONS = (m0002_bin_codes, m0003_key_roles, m0004_holds_and_scopes)

__all__ = ["MIGRATIONS", "MigrationError", "migrate"]


def migrate(store, now):
    """Bring store up to the newest schema; return the versions applied."""
    applied = []
    with store.lock:
        for module in sorted(MIGRATIONS, key=lambda module: module.VERSION):
            if module.VERSION <= store.schema_version:
                continue
            module.upgrade(store, now)
            store.schema_version = module.VERSION
            applied.append(module.VERSION)
    return applied
