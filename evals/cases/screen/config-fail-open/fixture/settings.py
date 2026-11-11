"""Runtime settings read from the environment."""
import os


class SettingsError(ValueError):
    pass


def retry_limit():
    """RETRY_LIMIT as a positive integer. Defaults to 3."""
    raw = os.environ.get("RETRY_LIMIT")
    if raw is None:
        return 3
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError(f"RETRY_LIMIT must be an integer, got {raw!r}") from None
    if value < 1:
        raise SettingsError(f"RETRY_LIMIT must be positive, got {value}")
    return value


def audit_enabled():
    """AUDIT_ENABLED as a boolean. Defaults to on."""
    raise NotImplementedError
