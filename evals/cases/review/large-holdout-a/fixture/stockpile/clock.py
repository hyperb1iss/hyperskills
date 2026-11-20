"""Time helpers. Every timestamp in the package is an aware UTC datetime."""
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def parse_timestamp(text):
    """Parse an ISO 8601 timestamp that carries a UTC offset; naive text is rejected."""
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        raise ValueError(f"timestamp {text!r} has no UTC offset")
    return value.astimezone(timezone.utc)


def format_timestamp(value):
    """Render an aware datetime as ISO 8601 in UTC; parse_timestamp reverses it exactly."""
    return value.astimezone(timezone.utc).isoformat()
