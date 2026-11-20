Incident summary: labelsmith, Nov 18

TL;DR: 14:02 deploy -> label renders failing at all three sites by 14:26; SEV-2 -> SEV-1; rolled back per the north test; central stayed down until the R2 purge (15:12). 2,340 parcels missed the 16:00 pickup, nearly all central; credits per the comp rule.

Timeline: 14:09 first alert (central) -> 14:15 SEV-2, Hesper leading -> 14:20 central on the paper fallback -> 14:26 north + coastal failing, SEV-1 -> 14:31 north test, north OK in 4 min -> 14:40 H2 ruled out -> 14:44 coastal rolled back, OK 14:49 -> 14:47 central rollback didn't take (R2 hosts) -> 15:05 `labelctl cache purge --site central --all` -> 15:12 central OK -> 15:20 SEV-3.

Cause: the glyph table issue; central also hit the R2 quirk.

Follow-ups: FU1 (Hesper, Dec 4); FU2 (render team, Nov 30); FU3 unchanged. Until FU1 ships, one region per day.

Status: all sites normal; paper fallback stood down 15:30.
