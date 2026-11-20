# Add document export

Adds `GET /tenants/{tenant}/docs/{doc}/export`, which renders a document as Markdown (the default) or JSON for download, so editors can move documents into other tools.

- `docvault/exporters.py` holds the formats. Each has a file extension, a content type, and a render function, so adding a format is one entry in `FORMATS`.
- `export_document` returns the filename, content type, and rendered content. An unknown `format` is a 400 that lists the supported names.
- The route requires a new `docs:export` scope, so tenants opt in by granting it.

Tests cover both formats, the default, an unknown format, the scope check, a cross-tenant path, and a missing document.
