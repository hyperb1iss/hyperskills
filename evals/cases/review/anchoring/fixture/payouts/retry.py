"""Backoff schedule for retrying transient gateway failures."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.5
    multiplier: float = 2.0
    max_delay: float = 8.0

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not 0 <= self.base_delay <= self.max_delay:
            raise ValueError("delays must satisfy 0 <= base_delay <= max_delay")

    def delay_after(self, attempt):
        """Seconds to wait after failed attempt number ``attempt``, counting from 1."""
        return min(self.base_delay * self.multiplier ** (attempt - 1), self.max_delay)


NO_RETRY = RetryPolicy(max_attempts=1)
