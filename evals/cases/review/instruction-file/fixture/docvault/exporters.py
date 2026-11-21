"""Export formats for documents."""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    extension: str
    content_type: str
    render: object


def to_markdown(doc):
    lines = [f"# {doc.title}", ""]
    if doc.tags:
        lines += ["Tags: " + ", ".join(doc.tags), ""]
    lines.append(doc.body.rstrip())
    return "\n".join(lines) + "\n"


def to_json(doc):
    return json.dumps(
        {
            "id": doc.id,
            "title": doc.title,
            "body": doc.body,
            "tags": list(doc.tags),
            "created_by": doc.created_by,
            "created_at": doc.created_at.isoformat(),
        },
        indent=2,
        sort_keys=True,
    )


FORMATS = {
    "markdown": Format("md", "text/markdown; charset=utf-8", to_markdown),
    "json": Format("json", "application/json", to_json),
}
