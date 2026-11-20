Hi Marit, here is where the help-center search migration stands before I'm out next week.

We are moving search in the customer portal from the old self-hosted cluster, Old Quarry, to the new managed index, Fernhall. We decided on Plan C: every change is written to both indexes, and reads move to Fernhall one tenant at a time through the per-tenant routing table. It is the only option that lets us roll back a single tenant. Brisa signed off on it in the architecture review.

The canary cohort, the 40 internal tenants plus 12 customer tenants who volunteered, already reads from Fernhall and has been stable.

The split-brain problem is fixed. Deletes made in the portal only reached Old Quarry, so deleted articles kept showing up in Fernhall results for canary tenants. Since the fix, Old Quarry's delete log is replayed into Fernhall every 10 minutes, and no deleted articles have reappeared.

One problem is still open, the 3% gap: for exact-phrase queries (queries in quotes), Fernhall returns about 3% fewer results than Old Quarry. It is not a blocker for the canary, but Brisa wants it under 1% before we move any tenant with more than 50,000 articles.

What I need from you:

- Clear the reindex retry queue before the Monday cutoff (Nov 23). The queue holds documents that failed to index in Fernhall, mostly attachments over 20 MB. As of this morning it had 1,870 items. After the cutoff, Old Quarry accepts no new tenants, and new tenants are created on Fernhall only.
- Do not touch the `portal-search` alias, which still sends search reads for most tenants to Old Quarry, until Brisa gives the go-ahead. She approves repointing it once the 3% gap is under 1% and the canary has run two clean weeks. We have had one so far.

Reach out if you have questions.
