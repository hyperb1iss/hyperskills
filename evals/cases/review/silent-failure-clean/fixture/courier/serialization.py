"""Wire format for outbox messages."""
import json


def encode(row, source):
    body = {"id": row.id, "topic": row.topic, "source": source, "data": row.payload}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode(raw):
    return json.loads(raw.decode("utf-8"))
