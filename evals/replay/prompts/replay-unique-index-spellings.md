The schema invariant check derives its UNIQUE indexes by replaying migration statements, and it misses two valid SurrealDB spellings. An index written with `COLUMNS` instead of `FIELDS` is not recognized at all, and one where `UNIQUE` is followed by another clause, such as `UNIQUE CONCURRENTLY`, is read as an ordinary index.

Make both spellings count as UNIQUE index requirements.
