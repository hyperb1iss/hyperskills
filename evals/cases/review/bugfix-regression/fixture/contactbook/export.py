"""Exports of a contact book: the browser download and on-disk backups."""

import io
import os
import tempfile
from dataclasses import dataclass

from .csvio import write_contacts


@dataclass(frozen=True)
class Download:
    filename: str
    content_type: str
    body: bytes

    def headers(self):
        return {
            "Content-Type": self.content_type,
            "Content-Disposition": f'attachment; filename="{self.filename}"',
            "Content-Length": str(len(self.body)),
        }


def download_response(book, today):
    """The file behind the contacts page's Download CSV button.

    People open it in spreadsheet apps. Integrations read contacts from the JSON API,
    never from this download.
    """
    buffer = io.StringIO()
    write_contacts(book.all(), buffer, bom=True)
    return Download(
        filename=f"contacts-{today.isoformat()}.csv",
        content_type="text/csv; charset=utf-8",
        body=buffer.getvalue().encode("utf-8"),
    )


def write_backup(book, path):
    """Write ``book`` to ``path`` for restore.restore_backup, replacing the file atomically."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            write_contacts(book.all(), fh)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
