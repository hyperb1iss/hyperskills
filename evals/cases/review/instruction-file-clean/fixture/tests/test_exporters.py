import json
import unittest
from datetime import datetime, timezone

from docvault.exporters import FORMATS, to_json, to_markdown
from docvault.models import Document

DOC = Document("doc_000042", "t-river", "Plan", "Step one.\n\n", "u-1", datetime(2026, 1, 2, tzinfo=timezone.utc))


class ExporterTests(unittest.TestCase):
    def test_markdown_without_tags(self):
        self.assertEqual(to_markdown(DOC), "# Plan\n\nStep one.\n")

    def test_json_round_trips(self):
        data = json.loads(to_json(DOC))
        self.assertEqual(data["created_at"], "2026-01-02T00:00:00+00:00")
        self.assertEqual(data["tags"], [])

    def test_formats_table(self):
        self.assertEqual({name: fmt.extension for name, fmt in FORMATS.items()}, {"markdown": "md", "json": "json"})


if __name__ == "__main__":
    unittest.main()
