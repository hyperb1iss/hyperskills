"""Runtime settings, read from the environment."""

import os
from dataclasses import dataclass


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    listen_port: int = 8080
    page_size: int = 50
    profile_cache_ttl: int = 300

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        return cls(
            listen_port=_int(env, "TEAMDIR_PORT", 8080, minimum=1),
            page_size=_int(env, "TEAMDIR_PAGE_SIZE", 50, minimum=1),
            profile_cache_ttl=_int(env, "TEAMDIR_PROFILE_CACHE_TTL", 300, minimum=0),
        )


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
