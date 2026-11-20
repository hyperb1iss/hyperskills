import unittest
from datetime import datetime, timezone
from decimal import Decimal

from courier.broker import Publisher
from courier.outbox import Outbox
from courier.relay import build_publisher, drain, relay_once
from courier.serialization import decode
from courier.settings import RelaySettings

NOON = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)


def clock():
    return NOON


class FakeClient:
    def __init__(self):
        self.batches = []

    @property
    def sent(self):
        return [(topic, message) for topic, batch in self.batches for message in batch]

    def send_batch(self, topic, messages):
        self.batches.append((topic, [decode(m) for m in messages]))


def outbox_with(count, topic="orders.created"):
    outbox = Outbox()
    for n in range(count):
        outbox.add(topic, {"n": n})
    return outbox


class RelayTests(unittest.TestCase):
    def test_publishes_pending_rows_in_order(self):
        outbox, client = outbox_with(3), FakeClient()
        self.assertEqual(relay_once(outbox, Publisher(client, "orders"), clock), 3)
        self.assertEqual([m["data"]["n"] for _, m in client.sent], [0, 1, 2])
        self.assertEqual(outbox.pending(10), [])
        self.assertEqual(outbox.get(1).published_at, NOON)

    def test_empty_outbox(self):
        self.assertEqual(relay_once(Outbox(), Publisher(FakeClient(), "orders"), clock), 0)

    def test_limit(self):
        outbox = outbox_with(5)
        relay_once(outbox, Publisher(FakeClient(), "orders"), clock, limit=2)
        self.assertEqual(len(outbox.pending(10)), 3)

    def test_message_names_its_source(self):
        client = FakeClient()
        relay_once(outbox_with(1), Publisher(client, "billing"), clock)
        self.assertEqual(client.sent[0][1]["source"], "billing")
        self.assertEqual(client.sent[0][1]["schema"], 2)

    def test_batches_split_by_topic_and_size(self):
        outbox, client = outbox_with(3), FakeClient()
        outbox.add("orders.paid", {"total": Decimal("19.90")})
        relay_once(outbox, Publisher(client, "orders", max_batch=2), clock)
        sizes = [(topic, len(batch)) for topic, batch in client.batches]
        self.assertEqual(sizes, [("orders.created", 2), ("orders.created", 1), ("orders.paid", 1)])
        self.assertEqual(client.sent[-1][1]["data"], {"total": "19.90"})

    def test_drain_stops_on_a_short_pass(self):
        settings = RelaySettings(poll_limit=2, max_batch=2)
        outbox, client = outbox_with(5), FakeClient()
        self.assertEqual(drain(outbox, build_publisher(client, settings), clock, settings), 5)
        self.assertEqual(len(client.batches), 3)


if __name__ == "__main__":
    unittest.main()
