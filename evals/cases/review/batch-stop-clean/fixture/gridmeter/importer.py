"""Load a vendor CSV drop into the reading store."""
import csv
from dataclasses import dataclass, field

from .parsing import RowError, parse_row


@dataclass
class ImportSummary:
    imported: int = 0
    rejected: list = field(default_factory=list)


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def import_file(path, store):
    """Parse every row of a drop, then write the good readings in one batch."""
    summary = ImportSummary()
    readings = []
    for line, row in enumerate(read_rows(path), start=2):
        try:
            readings.append(parse_row(row))
        except RowError as error:
            summary.rejected.append(f"line {line}: {error}")
    summary.imported = store.save_batch(readings)
    return summary
