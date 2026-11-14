`sibyld db duplicates` groups rows by the fields of each UNIQUE index, and it treats rows that have no value for one of those fields as duplicates of each other. SurrealDB does not index a key with a missing component, so those rows are legitimately distinct. Every user who never linked GitHub has no `github_id`, and `--collapse` would delete all but one of them.

Rows with a missing key component must never be grouped or collapsed. Values of different types are different keys too (1 and '1'). The keys reported for a group stay lists of the stringified values.
