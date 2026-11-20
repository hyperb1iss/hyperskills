# Working in docvault

docvault is the document service behind the workspace editor. Python 3.11 or later, standard library only.

## Layout

- `docvault/routes.py` maps request paths to handlers and checks scopes.
- `docvault/handlers.py` holds one function per endpoint; each returns `(status, body)`.
- `docvault/store.py` is the storage layer. All tenants share one store, keyed by document id.

## Conventions

- Handlers take `(store, principal, request, **path_params)` and return a 4xx tuple for client errors instead of raising.
- A new endpoint needs a route entry, a scope, and tests in `tests/`.
- Run the tests with `python -m unittest discover -s tests -t .` from the repository root.

## Review

- Keep review comments to behavior; formatting is not reviewed.
