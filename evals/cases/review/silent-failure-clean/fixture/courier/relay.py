"""Polls the outbox and publishes pending rows."""
from .broker import Publisher


def build_publisher(client, settings):
    return Publisher(client, settings.source, max_batch=settings.max_batch)


def relay_once(outbox, publisher, clock, limit=500):
    rows = outbox.pending(limit)
    if not rows:
        return 0
    published = publisher.publish(rows)
    outbox.mark_published(published, clock())
    return len(published)


def drain(outbox, publisher, clock, settings, max_passes=10):
    """Relay full pages until a pass comes back short or max_passes runs out.

    A timed-out batch also makes a pass short; the next scheduled drain retries it.
    """
    total = 0
    for _ in range(max_passes):
        sent = relay_once(outbox, publisher, clock, settings.poll_limit)
        total += sent
        if sent < settings.poll_limit:
            break
    return total
