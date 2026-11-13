"""Out-of-range reading removal."""
import logging

log = logging.getLogger("sensors")


def drop_invalid(readings):
    """Return the readings whose value is a number between -50 and 150. Out-of-range readings are discarded."""
    kept = []
    for reading in readings:
        value = reading.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not -50 <= value <= 150:
            log.warning("reading from %s discarded (value %r)", reading.get("sensor"), value)
            continue
        kept.append(reading)
    return kept
