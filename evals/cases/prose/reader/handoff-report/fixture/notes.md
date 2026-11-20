# Working log: duplicate usage rows in tallyhouse

## Mon 11/16

- Ticket from revenue assurance: some November invoices count the same usage event twice. Calling these "ghost rows" from here on: a usage row whose event_id already exists for that account.
- Count so far: 412 accounts have at least one ghost row. Ghost rows are about 0.8% of billed units for November.
- Hypotheses:
  - H1: an ingest worker retries a batch after the database committed it but before the ack came back. The ack timeout is 5 s.
  - H2: clock skew between ingest nodes makes the duplicate check miss.
  - H3: the hourly and daily rollups both count the same events while they overlap.
- Support also suggested the client library double-sending events, and packet loss between ingest and the database. Not pursued once H1 reproduced.
- H2: node clocks all agree within 40 ms, and the duplicate check uses event_id, not time. Ruled out.
- H3: the rollups write separate summary tables; the ghost rows are in the raw usage table itself. Ruled out as a cause, but see the T7 note on Wednesday.
- H1: reproduced on staging by delaying acks by 6 s. Every retried batch produced ghost rows. Confirmed.

## Tue 11/17

- Fix A: unique index on (account_id, event_id), so the second insert fails. Shipped to prod at 10:20.
- Rolled back Fix A at 11:05. Building the index locked the usage table on shard 9, the shard with our three largest tenants, for about 40 minutes, and ingest backed up. Index builds on shard 9 need an online build tool we don't have yet.
- Fix B: every batch carries a retry token. The server keeps tokens for 24 h and skips a batch whose token it has already committed. No index needed. PR 4471.
- Fix B is behind the flag tally.retry_token: on in staging, off in prod.

## Wed 11/18

- Staging soak with Fix B and the 6 s ack delay: zero new ghost rows over 18 h.
- T7 window: from 00:00 to 00:07 UTC the hourly rollup and the daily rollup run at the same time and the usage table is at peak load. Don't change ingest config inside it. Plan: enable Fix B in prod on Thursday after 00:07 UTC.
- Existing ghost rows still need deleting. Wrote the sweep: a script that deletes ghost rows and keeps the earliest copy of each. Only run as a dry run on staging so far.
- The sweep changes November invoiced totals, so Corwin (revenue assurance) has to sign off before it runs in prod. Asked him today; no answer yet.
- DUR = the daily usage report that revenue assurance receives each morning. After a dry run, compare the sweep's planned deletions against the DUR diff for the same days; they should match within rounding.
- Dry run command: tallyctl sweep --dry-run --month 2026-11
- Left the 6 s ack delay on staging ingest-2 for repro. It has to come off before Friday's staging release.
- Fix A can come back once we have an online index build. Not urgent; Fix B covers the problem.
- Handing off to Dagny tomorrow.
