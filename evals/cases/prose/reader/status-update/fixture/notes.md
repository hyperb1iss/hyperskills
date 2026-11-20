# Search migration notes

Context: help-center search in the customer portal is moving from the old self-hosted cluster ("Old Quarry") to the new managed index ("Fernhall"). Search reads go through the alias `portal-search`, which still points at Old Quarry for most tenants.

## Oct 28

- Options for the cutover:
  - Plan A: rebuild Fernhall from a nightly snapshot and switch every tenant at once.
  - Plan B: keep Old Quarry for tenants above 1M documents and move everyone else.
  - Plan C: write every change to both indexes, then move reads one tenant at a time by editing the per-tenant routing table.
- Leaning toward C: it is the only option with a per-tenant rollback.

## Nov 3

- Canary cohort: the 40 internal tenants plus 12 customer tenants who volunteered. Their reads come from Fernhall through the routing table.
- Found the "split-brain" problem: deletes made in the portal only reached Old Quarry, so deleted articles kept showing up in Fernhall results for canary tenants.

## Nov 5

- Fix merged: replay Old Quarry's delete log into Fernhall every 10 minutes. No deleted articles have reappeared since.

## Nov 10

- Decided on Plan C. Brisa signed off in the architecture review.
- "The 3% gap": for exact-phrase queries (queries in quotes), Fernhall returns about 3% fewer results than Old Quarry. Looks like a different tokenizer for hyphenated words. Not fixed. Everything else matches within 0.2%.
- Brisa: the gap has to be under 1% before we move any tenant with more than 50,000 articles.

## Nov 12

- RQ = the reindex retry queue: documents that failed to index in Fernhall, mostly attachments over 20 MB. 1,870 items as of this morning.
- The retry queue has to be empty before the Monday cutoff, otherwise those articles are missing for every tenant we move.
- Monday cutoff (Nov 23): the last day Old Quarry accepts new tenants. After that, new tenants are created on Fernhall only.
- Do not repoint `portal-search` to Fernhall globally yet. Brisa approves that once the 3% gap is under 1% and the canary has run two clean weeks. Clean weeks so far: one.

## Nov 13

- Handing the retry queue to Marit while I'm out next week. Marit hasn't worked on the migration before.
