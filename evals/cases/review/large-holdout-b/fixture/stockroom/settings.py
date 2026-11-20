"""Runtime settings, read from the environment."""

import os
from dataclasses import dataclass


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    low_stock_threshold: int = 5
    max_adjustment: int = 1000
    reservation_ttl: int = 900
    max_reservation_ttl: int = 86400
    warehouse_priority: tuple = ()

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        settings = cls(
            low_stock_threshold=_int(env, "STOCKROOM_LOW_STOCK_THRESHOLD", 5, minimum=0),
            max_adjustment=_int(env, "STOCKROOM_MAX_ADJUSTMENT", 1000, minimum=1),
            reservation_ttl=_int(env, "STOCKROOM_RESERVATION_TTL", 900, minimum=1),
            max_reservation_ttl=_int(env, "STOCKROOM_MAX_RESERVATION_TTL", 86400, minimum=1),
            warehouse_priority=_list(env, "STOCKROOM_WAREHOUSE_PRIORITY"),
        )
        if settings.reservation_ttl > settings.max_reservation_ttl:
            raise SettingsError("STOCKROOM_RESERVATION_TTL exceeds STOCKROOM_MAX_RESERVATION_TTL")
        return settings


def _int(env, name, default, minimum):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise SettingsError(f"{name} must be at least {minimum}, got {value}")
    return value


def _list(env, name):
    raw = env.get(name, "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())
