# Batch outbox publishing

The relay now publishes pending rows through the broker's batch API instead of one request per row. Rows are grouped by topic and sent in batches of up to `COURIER_MAX_BATCH` (default 100), which turns a backlog of 20,000 order events from about 20,000 broker requests into about 200. A batch that times out no longer aborts the whole pass: it stays pending together with the rest of its topic, which keeps each topic in id order, and the other topics in that pass carry on.

`drain()` relays full pages, up to ten passes per call, until a pass comes back short, which is also what happens after a timeout; the next scheduled drain picks the held topic up again.
