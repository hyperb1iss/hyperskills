# Incident summary: label printing outage, Nov 18

**Summary.** A release of labelsmith, the service that renders shipping labels for our three regional warehouses (north, central, and coastal), broke label printing at all three sites on Nov 18. North and coastal recovered after a rollback; central stayed down until 15:12. 2,340 parcels missed the 16:00 carrier pickup, nearly all of them from central. Under the standard late-delivery policy, customers with next-day service on those parcels get a full shipping refund; standard orders get no credit.

**Cause.** The release, labelsmith 3.14, added a new barcode font pack. The font pack referenced a glyph table that only exists on hosts provisioned after September, so every older host failed to render labels. Central runs on the oldest render hosts (the R2 hosts), which keep their font cache across versions. Rolling back therefore did not fix central until the cache was cleared by hand.

**Timeline.**

- 14:02 labelsmith 3.14 deployed to all regions.
- 14:09 first alert: label render errors at central.
- 14:15 incident opened as SEV-2 (one site degraded, workaround available), with Hesper as incident lead.
- 14:20 central switched to its paper fallback, writing shipping manifests by hand at roughly a third of normal throughput.
- 14:26 north and coastal also failing; raised to SEV-1 (more than one site down).
- 14:31 rolled north back to the previous version to test whether the font pack was the cause; north recovered in 4 minutes.
- 14:40 ruled out the other suspect, a printer firmware update scheduled for the same day: it had not started at any site.
- 14:44 rolled back coastal; it recovered at 14:49.
- 14:47 central's rollback did not help, because the R2 hosts kept the 3.14 font cache.
- 15:05 cleared that cache with `labelctl cache purge --site central --all`.
- 15:12 central recovered.
- 15:20 lowered to SEV-3 for cleanup.

**Follow-ups.**

- Add a deploy-pipeline check that prints a test label on one host of each host generation before rollout. Owner: Hesper, due Dec 4.
- Make rollback clear the font cache. Owner: render team, due Nov 30.
- Retire the R2 hosts, already planned for Q1, with no change to that date.

Until the pipeline check ships, labelsmith deploys go to one region per day instead of all regions at once.

**Status.** All three warehouses are operating normally. The paper fallback was stood down at 15:30.
