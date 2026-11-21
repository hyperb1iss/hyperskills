"""Settings, read from the environment."""

import os
from dataclasses import dataclass


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    sender: str = "Notifications <notify@example.invalid>"
    relay_url: str = "smtp://relay.example.invalid:25"
    relay_timeout_seconds: int = 10
    digest_sender: str = "Your digest <digest@example.invalid>"
    digest_max_events: int = 50
    digest_lookback_days: int = 14
    digest_ledger_path: str = "/var/lib/digests/ledger.json"
    preferences_url: str = "https://app.example.invalid/settings/notifications"

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        defaults = cls()
        return cls(
            sender=env.get("NOTIFY_SENDER", defaults.sender),
            relay_url=env.get("NOTIFY_RELAY_URL", defaults.relay_url),
            relay_timeout_seconds=_int(env, "NOTIFY_RELAY_TIMEOUT", defaults.relay_timeout_seconds, minimum=1),
            digest_sender=env.get("DIGEST_SENDER", defaults.digest_sender),
            digest_max_events=_int(env, "DIGEST_MAX_EVENTS", defaults.digest_max_events, minimum=1),
            digest_lookback_days=_int(env, "DIGEST_LOOKBACK_DAYS", defaults.digest_lookback_days, minimum=7),
            digest_ledger_path=env.get("DIGEST_LEDGER_PATH", defaults.digest_ledger_path),
            preferences_url=env.get("PREFERENCES_URL", defaults.preferences_url),
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
