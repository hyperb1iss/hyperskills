"""Relay settings from the environment."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RelaySettings:
    source: str = "orders"
    poll_limit: int = 500
    max_batch: int = 100

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        return cls(
            source=env.get("COURIER_SOURCE", "orders"),
            poll_limit=_positive_int(env, "COURIER_POLL_LIMIT", 500),
            max_batch=_positive_int(env, "COURIER_MAX_BATCH", 100),
        )


def _positive_int(env, name, default):
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None
    if value < 1:
        raise ValueError(f"{name} must be at least 1, got {value}")
    return value
