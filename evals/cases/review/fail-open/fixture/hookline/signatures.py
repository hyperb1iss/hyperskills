"""HMAC signatures on incoming webhooks.

Header format: "t=<unix seconds>,v1=<hex HMAC-SHA256 of '<t>.<body>'>". A sender
that is rotating its secret repeats v1, once per secret.
"""
import hashlib
import hmac


MAX_SIGNATURES = 8


class SignatureError(Exception):
    pass


def sign(secret, timestamp, body):
    message = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def parse_header(value):
    fields = {}
    for part in value.split(","):
        key, _, item = part.strip().partition("=")
        fields.setdefault(key, []).append(item)
    return fields


def _header(headers, name):
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def verify(provider, headers, body, now):
    fields = parse_header(_header(headers, provider.header))
    try:
        timestamp = int(fields["t"][0])
    except (KeyError, ValueError):
        raise SignatureError("missing or malformed timestamp") from None
    if abs(now - timestamp) > provider.tolerance:
        raise SignatureError("timestamp outside tolerance")
    candidates = fields.get("v1", [])
    if len(candidates) > MAX_SIGNATURES:
        raise SignatureError("too many signatures")
    expected = [sign(secret, timestamp, body) for secret in provider.secrets]
    if candidates and not any(hmac.compare_digest(c, e) for c in candidates for e in expected):
        raise SignatureError("signature mismatch")
