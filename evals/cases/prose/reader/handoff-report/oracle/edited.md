# Handoff: duplicate usage rows in tallyhouse

Dagny, here is where the duplicate usage work stands and what is left for you.

## Problem and cause

Some November invoices count the same usage event twice. I have been calling these duplicates "ghost rows": usage rows whose event_id already exists for that account. They affect 412 accounts and make up about 0.8% of November's billed units.

The cause is ingest retries. When the database commits a batch but its acknowledgment does not arrive within the timeout, the ingest worker sends the batch again and its events are stored twice. I confirmed this on staging by delaying acknowledgments by 6 seconds.

Two other suspects are ruled out. Clock skew between ingest nodes is not the cause: the clocks agree within 40 ms, and the duplicate check uses event_id, not time. The hourly and daily rollups are not the cause either, because the duplicates are already in the raw usage table.

## Fixes

The first fix added a unique index on (account_id, event_id). I rolled it back on Tuesday: building the index locked the usage table on shard 9, the shard that holds our three largest tenants, for about 40 minutes, and ingest backed up. It can come back later. That is not urgent, because the second fix covers the problem.

The second fix is PR 4471. It attaches a retry token to every batch, and the server skips a batch whose token it has already committed. It is behind the flag `tally.retry_token`, which is on in staging and off in production. An 18-hour staging soak with the 6-second delay produced zero new duplicates.

## What is left for you

1. Turn on `tally.retry_token` in production on Thursday after 00:07 UTC. From 00:00 to 00:07 UTC the hourly and daily rollups run at the same time and the usage table is at peak load, so do not change ingest settings inside that window.
2. Delete the existing duplicates with the sweep, a script that deletes them and keeps the earliest copy of each. It has only been dry-run on staging. Do NOT run it in production without approval from Corwin in revenue assurance, because it changes November invoiced totals.
3. Run it in this order: a production dry run with `tallyctl sweep --dry-run --month 2026-11`; compare its planned deletions against the daily usage report that revenue assurance receives each morning, which should match within rounding; get Corwin's approval; then do the real run.

I asked Corwin on Wednesday and have no reply yet. If he is still quiet by Thursday noon, follow up with him.

The 6-second acknowledgment delay is still on staging ingest-2 for reproducing the bug. Remove it before Friday's staging release.
