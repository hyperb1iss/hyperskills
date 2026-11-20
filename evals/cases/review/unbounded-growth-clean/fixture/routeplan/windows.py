"""Customer delivery windows."""
from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class Window:
    start: time
    end: time

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError(f"window must end after it starts: {self.start}-{self.end}")

    def contains(self, moment):
        return self.start <= moment < self.end


def parse_window(text):
    """Parse '09:00-12:30'. A blank value means any time of day."""
    text = text.strip()
    if not text:
        return Window(time(0, 0), time(23, 59))
    try:
        start, end = (time.fromisoformat(part.strip()) for part in text.split("-"))
    except ValueError:
        raise ValueError(f"not a delivery window: {text!r}") from None
    return Window(start, end)


def overlap(a, b):
    """Return the shared part of two windows, or None when they do not meet."""
    start, end = max(a.start, b.start), min(a.end, b.end)
    if start >= end:
        return None
    return Window(start, end)
