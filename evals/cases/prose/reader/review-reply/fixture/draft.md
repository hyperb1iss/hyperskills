Thanks for the review, all six addressed:

1. Fixed.
2. Done, the clamp lives in the loader now. Option 2 was worse for the reasons in my notes; option 3 doesn't fix existing rows.
3. Keeping the double read for now. Dropping it needs the backfill first (QX-2, week of Dec 7). I'll follow up once that lands.
4. Went with `quota_floor`. `min_quota` is taken in the legacy file and means something else there.
5. The flake was the clock thing, not this change. Pinned it with the freeze helper; 0/200 now, was about 1/30.
6. Zero-quota teams now get QUOTA_EXHAUSTED; unset goes through the fallback path. The eleven teams this affects are fine per the owners list.

Ships dark behind the flag, staging cluster first, then one cluster at a time. Tobin, adding you as second reviewer for the scheduler side; the loader change is the part I'd most like eyes on, since that's where the clamp moved and where the zero and unset cases now split. Happy to walk through any of it.
