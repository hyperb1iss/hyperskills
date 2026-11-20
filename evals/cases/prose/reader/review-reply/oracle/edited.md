Thanks for the review. All six comments are addressed.

For context, this PR changes how harborjobs reads team quotas. A configured quota of 0 used to be read as "unset", so those teams got unlimited jobs. Now 0 means zero jobs, and unset still means the default quota of 25.

1. Docstring typo: fixed.
2. Clamp location: done, the clamp now lives in the config loader instead of the scheduler, so every caller gets clamped values. I rejected the second option, clamping in both the scheduler and the admin API, because it keeps two copies of the rule and the admin API would still show unclamped values. The third option, validating only when a quota is written, doesn't fix existing rows.
3. Double read: we read each team's quota from both the legacy `teams.yaml` file and the new quota table, and the table's value wins when both have one. I'm keeping that for now. Dropping the legacy read needs the backfill first, which copies the 214 teams that only exist in the legacy file into the quota table (QX-2, platform data team, week of Dec 7). I'll follow up once that lands.
4. Naming: went with `quota_floor`. `min_quota` is taken in the legacy file, where it means the minimum number of runners reserved for a team.
5. Flaky `test_quota_reload`: not caused by this change. The test compared wall-clock timestamps and failed when a reload crossed a second boundary. I pinned the clock with the freeze helper; it fails 0/200 runs now, was about 1/30.
6. Zero-quota path: teams with a quota of 0 now get QUOTA_EXHAUSTED. A team with no quota set goes through the fallback path, which applies the default of 25. Eleven teams have a quota of 0 today. All eleven are archived teams, confirmed against the owners list, so blocking their jobs is intended.

The change ships dark behind the flag `quota.zero_means_zero` (default off), turned on for the staging cluster first, then one cluster at a time.

Tobin, I'm adding you as second reviewer for the scheduler side. The loader change is the part I'd most like eyes on, since that's where the clamp moved and where the zero and unset cases now split. Happy to walk through any of it.
