"""Stale reading removal."""
import logging

log = logging.getLogger("sensors")


def drop_stale(readings, cutoff):
    """Return the readings taken at or after cutoff. Older readings are discarded."""
    fresh = []
    for reading in readings:
        if reading["at"] < cutoff:
            log.warning("stale reading from %s discarded (taken at %s)", reading["sensor"], reading["at"])
            continue
        fresh.append(reading)
    return fresh
