"""Append-only log of stock movements, read by the audit export."""


class EventLog:
    def __init__(self):
        self._events = []

    def record(self, event):
        self._events.append(event)

    def since(self, when):
        return [event for event in self._events if event.at > when]

    def of_kind(self, kind):
        return [event for event in self._events if event.kind == kind]

    def __len__(self):
        return len(self._events)


EXPORT_FIELDS = ("at", "kind", "sku", "warehouse", "quantity", "detail")


def export_rows(events):
    """Rows for the audit export, oldest first, timestamps in ISO 8601."""
    return [
        (event.at.isoformat(), event.kind, event.sku, event.warehouse_id, event.quantity, event.detail)
        for event in sorted(events, key=lambda event: event.at)
    ]
