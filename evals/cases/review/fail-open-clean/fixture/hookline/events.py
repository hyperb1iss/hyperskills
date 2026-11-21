"""Applying provider events to the payments ledger."""

HANDLED = {
    "kestrel": {"payment.settled", "payment.refunded"},
    "osprey": {"transfer.completed", "transfer.reversed"},
}


class Ledger:
    """In-memory stand-in for the processed_events and ledger_entries tables."""

    def __init__(self):
        self.processed = set()
        self.entries = []

    def apply(self, provider, event_id, kind, data):
        self.processed.add((provider, event_id))
        self.entries.append({"provider": provider, "event": event_id, "kind": kind, "data": data})


def dispatch(provider, event, ledger):
    event_id, kind = event.get("id"), event.get("type")
    if not event_id or not kind:
        return 400, {"error": "event needs id and type"}
    if (provider, event_id) in ledger.processed:
        return 200, {"status": "duplicate"}
    if kind not in HANDLED.get(provider, set()):
        return 202, {"status": "ignored"}
    ledger.apply(provider, event_id, kind, event.get("data", {}))
    return 200, {"status": "applied"}
