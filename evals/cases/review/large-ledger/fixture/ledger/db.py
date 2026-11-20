"""Row storage: named tables of plain dicts, saved as one JSON file.

The models in the other modules are built from these rows. Migrations in
ledger.migrations change rows in place and advance schema_version.
"""
import json
from pathlib import Path


class Store:
    def __init__(self, tables=None, schema_version=0):
        self.tables = tables if tables is not None else {}
        self.schema_version = schema_version

    def table(self, name):
        return self.tables.setdefault(name, [])

    def insert(self, name, row):
        rows = self.table(name)
        row = dict(row)
        row.setdefault("id", max((r["id"] for r in rows), default=0) + 1)
        rows.append(row)
        return row

    def select(self, name, **where):
        return [row for row in self.table(name) if all(row.get(k) == v for k, v in where.items())]

    def one(self, name, **where):
        rows = self.select(name, **where)
        if len(rows) != 1:
            raise LookupError(f"expected one {name} row for {where}, found {len(rows)}")
        return rows[0]

    def save(self, path):
        data = {"schema_version": self.schema_version, "tables": self.tables}
        Path(path).write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["tables"], data["schema_version"])
