Creating an entity through the API with no authenticated user drops a payload-supplied `principal_id` from scoped metadata, so a private row cannot be bound to a caller-chosen identity. Retrieval resolves a private row's owner as `principal_id` or `scope_key`, though, and a `scope_key` from the payload still gets through.

With no authenticated user, drop both `principal_id` and `scope_key` from the stored metadata.
