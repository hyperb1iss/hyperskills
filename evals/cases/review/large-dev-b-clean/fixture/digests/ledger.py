"""Where each user's last digest window ended.

The ledger is one JSON object mapping user id to an ISO timestamp. ``save``
replaces the file atomically, so a crash leaves either the old file or the new
one, never a partial write.
"""

import json
import os
import tempfile
from datetime import datetime


class DigestLedger:
    def __init__(self, path=None):
        self._path = path
        self._cutoffs = {}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                raw = json.load(fh)
            self._cutoffs = {user_id: datetime.fromisoformat(value) for user_id, value in raw.items()}

    def cutoff_for(self, user_id):
        """End of the user's last recorded window, or None before their first digest."""
        return self._cutoffs.get(user_id)

    def record(self, user_id, cutoff):
        self._cutoffs[user_id] = cutoff

    def save(self):
        if self._path is None:
            return
        directory = os.path.dirname(os.path.abspath(self._path))
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({key: value.isoformat() for key, value in sorted(self._cutoffs.items())}, fh, indent=1)
            os.replace(tmp_path, self._path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
