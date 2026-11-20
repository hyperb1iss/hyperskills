# Notes: PR 2208, per-team quota floor (harborjobs)

Goal: in harborjobs, a team with a configured quota of 0 currently gets unlimited jobs, because the loader reads 0 as "unset". Make 0 mean zero jobs, and keep unset meaning the default quota of 25.

## Review round 1 (Odile, 6 comments)

1. Typo in the loader docstring. Fixed.
2. Wants the clamp moved out of the scheduler and into the config loader, so every caller gets clamped values. Agreed; moved.
3. Asks why I kept the double read. We read each team's quota from both the legacy `teams.yaml` and the new quota table, and use the table's value when both have one. Removing the legacy read needs the backfill first: copying the 214 teams that only exist in `teams.yaml` into the quota table. Ticket QX-2, owned by the platform data team, scheduled for the week of Dec 7.
4. Asks to rename `min_quota` because the name is unclear. Can't use `min_quota` anyway: the legacy `teams.yaml` already has a `min_quota` field that means the minimum number of runners reserved for a team. Went with `quota_floor`.
5. `test_quota_reload` is flaky. Not my change: the test compares wall-clock timestamps and fails when a reload crosses a second boundary. Pinned the clock with the freeze helper. 0/200 failures now; it was about 1/30 before.
6. Asks about the zero-quota path. With the clamp in the loader, a quota of 0 now reaches the scheduler as 0 and the team's jobs are rejected with QUOTA_EXHAUSTED. An unset quota goes through the fallback path, which applies the default of 25.

## Where to put the clamp (comment 2)

- Option 1: clamp in the config loader. Chosen.
- Option 2: clamp in the scheduler and again in the admin API. Rejected: two copies of the same rule, and the admin API would still show unclamped values.
- Option 3: validate only when a quota is written. Rejected: existing bad rows in the quota table would never be fixed.

## Other

- Eleven teams have a quota of 0 today. All eleven are archived teams; confirmed against the owners list. After this change they can't run jobs, which is intended.
- Rollout: behind the flag `quota.zero_means_zero`, default off. Turned on one cluster at a time, starting with the staging cluster.
- Second reviewer requested: Tobin, from the scheduler team. Tobin hasn't seen round 1.
