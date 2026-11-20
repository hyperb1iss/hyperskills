# Incident working notes: label printing outage, Nov 18

Service: labelsmith, which renders shipping labels for the three regional warehouses (north, central, coastal).

## Timeline

- 14:02 labelsmith 3.14 deployed to all regions. Its main change is the new barcode font pack.
- 14:09 first alert: label render errors at central. Error rate climbing.
- 14:15 incident opened as SEV-2 (one site degraded, workaround exists). Incident lead: Hesper.
- 14:20 central switches to the paper fallback: writing shipping manifests by hand. Throughput on paper is roughly a third of normal.
- 14:26 north and coastal also failing. Raised to SEV-1 (more than one site down).
- 14:31 hypothesis 1: the font pack. Rolled north back to 3.13 as a test ("the north test"). North recovered in 4 min.
- 14:40 hypothesis 2: the printer firmware update scheduled for the same day. Checked: the update had not started at any site. Ruled out.
- 14:44 rolled back coastal. Recovered 14:49.
- 14:47 central rollback did not help. Central runs on the older render hosts ("the R2 hosts"), which kept the 3.14 font cache after the rollback.
- 15:05 cleared the R2 font cache by hand: labelctl cache purge --site central --all
- 15:12 central recovered.
- 15:20 lowered to SEV-3 for cleanup.
- 15:30 paper fallback stood down.

## Impact

- 2,340 parcels missed the 16:00 carrier pickup, nearly all from central.
- Credits follow the standard late-delivery policy, which we kept calling "the comp rule": a full shipping refund for next-day orders, nothing for standard orders.

## Root cause

- The 3.14 font pack referenced a glyph table that only exists on hosts provisioned after September. Every host provisioned before then failed to render labels.
- The R2 hosts also cache fonts across versions, which is why rolling back did not fix central.

## Follow-ups

- FU1: add a check to the deploy pipeline that prints a test label on one host of each host generation before rollout. Owner: Hesper. Due Dec 4.
- FU2: make rollback clear the font cache. Owner: render team. Due Nov 30.
- FU3: retire the R2 hosts. Already planned for Q1; no date change.
- Decision: until FU1 ships, labelsmith deploys go to one region per day instead of all regions at once.

## Status

All three warehouses normal. The summary goes to the operations director, who was not in the incident channel.
