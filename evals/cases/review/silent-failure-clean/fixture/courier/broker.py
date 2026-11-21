"""Publishing outbox rows to the message broker."""
import logging
from itertools import groupby

from .serialization import encode

log = logging.getLogger(__name__)


class BrokerTimeout(Exception):
    """The broker did not acknowledge in time; the message may or may not be stored."""


def _chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


class Publisher:
    def __init__(self, client, source, max_batch=100):
        if max_batch < 1:
            raise ValueError("max_batch must be at least 1")
        self.client = client
        self.source = source
        self.max_batch = max_batch

    def publish(self, rows):
        """Send rows in per-topic batches; returns the ids the broker acknowledged.

        A topic stops at its first unacknowledged batch, so that batch and the
        rest of the topic stay pending and keep their order.
        """
        acknowledged = []
        ordered = sorted(rows, key=lambda row: (row.topic, row.id))
        for topic, group in groupby(ordered, key=lambda row: row.topic):
            acknowledged.extend(self._publish_topic(topic, list(group)))
        return acknowledged

    def _publish_topic(self, topic, rows):
        sent = []
        for batch in _chunks(rows, self.max_batch):
            try:
                self.client.send_batch(topic, [encode(row, self.source) for row in batch])
            except BrokerTimeout:
                log.warning("broker timed out on %d outbox rows for %s; holding the topic", len(batch), topic)
                break
            sent.extend(row.id for row in batch)
        return sent
