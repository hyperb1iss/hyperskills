import logging
import unittest
from datetime import datetime, timezone

from courier.broker import BrokerTimeout, Publisher
from courier.outbox import Outbox
from courier.relay import relay_once


class TimingOutClient:
    def __init__(self, failing_topic):
        self.failing_topic = failing_topic
        self.delivered = []

    def send_batch(self, topic, messages):
        if topic == self.failing_topic:
            raise BrokerTimeout(topic)
        self.delivered.extend(messages)


class AcknowledgementProof(unittest.TestCase):
    def test_rows_in_a_timed_out_batch_stay_pending(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        outbox = Outbox()
        outbox.add("orders.created", {"n": 1})
        outbox.add("orders.paid", {"n": 2})
        publisher = Publisher(TimingOutClient("orders.paid"), "orders")
        published = relay_once(outbox, publisher, lambda: datetime(2026, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(published, 1)
        self.assertEqual([row.topic for row in outbox.pending(10)], ["orders.paid"])


if __name__ == "__main__":
    unittest.main()
