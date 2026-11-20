# Batch geocoding and remembered misses

Route planning used to geocode each stop with its own request. `GeocodeClient.lookup_many` now sends every cache miss in a route to the geocoding service's batch endpoint in one call, and `plan_route` uses it, so a 60-stop route costs at most one backend request.

Addresses the service cannot place are remembered for an hour (`unknown_ttl`), so a route that is re-planned while a dispatcher fixes a typo does not query the backend again for the same bad stop. `GeoCache.stats()` reports entries, remembered misses, hits, and misses for the worker metrics page.

Normalization now drops a trailing unit designator (`Apt 4`, `Suite 3`, `#12`), since units in one building geocode to the same point and should share a cache entry.
