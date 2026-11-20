"""API keys: authentication, role checks, and warehouse scopes.

A request carries "Authorization: Bearer <key_id>.<secret>". The store keeps
only a SHA-256 digest of the secret, compared in constant time. Roles rank
viewer < operator < admin, and each action names the least role allowed to
perform it. A key's scope lists the warehouses it may act in; "*" stands for
every warehouse.
"""
import hashlib
import hmac
import secrets
from dataclasses import dataclass

VIEWER, OPERATOR, ADMIN = "viewer", "operator", "admin"
ROLE_RANK = {VIEWER: 0, OPERATOR: 1, ADMIN: 2}
REQUIRED_ROLE = {
    "view": VIEWER,
    "reserve": OPERATOR,
    "confirm": OPERATOR,
    "cancel": OPERATOR,
    "pick": OPERATOR,
}
WILDCARD = "*"


class Unauthorized(Exception):
    """The request did not prove which key sent it."""


class Forbidden(Exception):
    """The key is known but may not do what it asked."""


@dataclass(frozen=True)
class ApiKey:
    key_id: str
    role: str
    warehouses: tuple = ()


def _digest(secret):
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def normalize_scope(warehouses):
    """Return a scope as a sorted tuple of distinct warehouse ids.

    "*" cannot be combined with named warehouses. An empty scope is valid: the
    key authenticates but may not act in any warehouse until it is given one.
    """
    items = None if isinstance(warehouses, str) else list(warehouses)
    if items is None or not all(isinstance(item, str) and item.strip() for item in items):
        raise ValueError("warehouses must be a list of nonempty warehouse ids")
    scope = tuple(sorted({item.strip() for item in items}))
    if WILDCARD in scope and len(scope) > 1:
        raise ValueError('"*" cannot be combined with named warehouses')
    return scope


def issue_key(store, role, warehouses=()):
    """Create a key and return (ApiKey, token); the token is shown once and not stored."""
    if role not in ROLE_RANK:
        raise ValueError(f"unknown role {role!r}")
    scope = normalize_scope(warehouses)
    key_id = "key-" + secrets.token_hex(4)
    secret = secrets.token_urlsafe(24)
    store.put_key({"key_id": key_id, "role": role, "digest": _digest(secret), "revoked": False,
                   "warehouses": list(scope)})
    return ApiKey(key_id, role, scope), f"{key_id}.{secret}"


def set_scope(store, key_id, warehouses):
    """Replace a key's scope; it applies from the key's next request."""
    scope = list(normalize_scope(warehouses))
    with store.lock:
        row = store.key_row(key_id)
        if row is None:
            raise LookupError(f"no key {key_id}")
        row["warehouses"] = scope
        store.put_key(row)


def revoke_key(store, key_id):
    row = store.key_row(key_id)
    if row is None:
        raise LookupError(f"no key {key_id}")
    row["revoked"] = True
    store.put_key(row)


def authenticate(store, header):
    """Return the ApiKey an Authorization header proves, or raise Unauthorized."""
    if not isinstance(header, str) or not header.startswith("Bearer "):
        raise Unauthorized("missing bearer token")
    key_id, dot, secret = header[len("Bearer "):].strip().partition(".")
    if not dot or not key_id or not secret:
        raise Unauthorized("malformed bearer token")
    row = store.key_row(key_id)
    if row is None or row["revoked"] or not hmac.compare_digest(row["digest"], _digest(secret)):
        raise Unauthorized("unknown key, revoked key, or wrong secret")
    return ApiKey(row["key_id"], row["role"], tuple(row.get("warehouses", ())))


def require_role(key, action):
    """Raise Forbidden unless the key's role may perform action."""
    needed = REQUIRED_ROLE[action]
    if ROLE_RANK[key.role] < ROLE_RANK[needed]:
        raise Forbidden(f"key {key.key_id} needs the {needed} role to {action}")


def authorize(key, action, warehouse_id):
    """Raise Forbidden unless key may perform action in warehouse_id.

    The key's role must allow the action and warehouse_id must be in its scope.
    """
    require_role(key, action)
    scope = key.warehouses
    if WILDCARD not in scope and warehouse_id not in scope:
        raise Forbidden(f"key {key.key_id} is not scoped to warehouse {warehouse_id}")
