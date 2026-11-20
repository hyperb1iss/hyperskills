# Cache profile reads

Profile lookups are the hottest path in the directory API: every page header and every mention renders one, and each lookup goes to the store. This wires the `TTLCache` from `teamdir/cache.py` (added in the previous change) in front of `DirectoryService.get_profile`.

- `DirectoryService` takes an optional cache. Reads go through it, and `update_profile` drops the cached entry so the next read returns the new values. Without a cache argument the service uses `NullCache` and behaves as before.
- New setting `TEAMDIR_PROFILE_CACHE_TTL` in seconds, default 300; `0` turns the cache off. `build_service` reads it.
- The directory API runs as a single process serving one request at a time, so a process-local cache sees every write.

Tests cover cache hits in the service, invalidation on update, and the new setting.
