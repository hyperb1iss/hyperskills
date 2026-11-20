"""Wire format for outbox messages."""
import json
from datetime import datetime
from decimal import Decimal

SCHEMA_VERSION = 2


def _jsonable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"cannot encode {type(value).__name__}")


def encode(row, source):
    body = {"schema": SCHEMA_VERSION, "id": row.id, "topic": row.topic, "source": source, "data": row.payload}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=_jsonable).encode("utf-8")


def decode(raw):
    return json.loads(raw.decode("utf-8"))
