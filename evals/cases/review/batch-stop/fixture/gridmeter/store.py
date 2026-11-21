"""Reading storage. One row per meter and timestamp; a later write replaces an earlier one."""


class ReadingStore:
    def __init__(self):
        self._rows = {}
        self.writes = 0

    def save(self, reading):
        self._rows[(reading.meter_id, reading.taken_at)] = reading
        self.writes += 1

    def save_batch(self, readings):
        """Write readings in one round trip; returns how many were not already stored."""
        fresh = {(r.meter_id, r.taken_at): r for r in readings}
        if not fresh:
            return 0
        new = sum(1 for key in fresh if key not in self._rows)
        self._rows.update(fresh)
        self.writes += 1
        return new

    def count(self):
        return len(self._rows)

    def for_meter(self, meter_id):
        rows = [r for r in self._rows.values() if r.meter_id == meter_id]
        return sorted(rows, key=lambda r: r.taken_at)
