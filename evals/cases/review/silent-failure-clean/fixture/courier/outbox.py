"""Transactional outbox: rows are written with the business change and published later.

A row stays pending until a publisher reports it acknowledged, so delivery is
at-least-once and consumers deduplicate on the row id.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OutboxRow:
    id: int
    topic: str
    payload: dict
    published_at: Optional[datetime] = None


class Outbox:
    def __init__(self):
        self._rows = {}
        self._next_id = 1

    def add(self, topic, payload):
        row = OutboxRow(self._next_id, topic, payload)
        self._rows[row.id] = row
        self._next_id += 1
        return row

    def get(self, row_id):
        return self._rows[row_id]

    def pending(self, limit):
        rows = [row for row in self._rows.values() if row.published_at is None]
        return sorted(rows, key=lambda row: row.id)[:limit]

    def mark_published(self, ids, at):
        for row_id in ids:
            self._rows[row_id].published_at = at

    def purge_published(self, before):
        """Delete rows published before the cutoff; returns how many were removed."""
        old = [row.id for row in self._rows.values() if row.published_at is not None and row.published_at < before]
        for row_id in old:
            del self._rows[row_id]
        return len(old)
