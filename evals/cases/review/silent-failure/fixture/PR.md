# Batch outbox publishing

The relay now publishes pending rows through the broker's batch API instead of one request per row. Rows are grouped by topic and sent in batches of up to `COURIER_MAX_BATCH` (default 100), which turns a backlog of 20,000 order events from about 20,000 broker requests into about 200. A batch that times out is logged and the relay moves on to the next batch instead of abandoning the rest of the pass. `drain()` relays full pages until a pass comes back short, so the scheduler no longer needs its own loop.

Messages move to schema 2. Order payloads carry `Decimal` totals and `datetime` timestamps, which used to make `json.dumps` fail; they are now encoded as strings, and the new `schema` field lets consumers tell the two formats apart.
