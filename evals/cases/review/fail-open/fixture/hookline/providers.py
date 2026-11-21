"""Webhook senders we accept, keyed by the path segment they post to."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    name: str
    secrets: tuple
    header: str
    tolerance: int = 300


def _required(env, name):
    """Comma-separated; during a rotation both the old and the new secret are listed."""
    values = tuple(part.strip() for part in env.get(name, "").split(",") if part.strip())
    if not values:
        raise KeyError(f"{name} is not set")
    return values


def load_providers(env):
    return {
        "kestrel": Provider("kestrel", _required(env, "KESTREL_SIGNING_SECRET"), "Kestrel-Signature"),
        "osprey": Provider("osprey", _required(env, "OSPREY_SIGNING_SECRET"), "Osprey-Signature", tolerance=600),
    }
