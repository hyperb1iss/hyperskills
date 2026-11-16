Restoring a backup normalizes each entity's owner metadata through the shared memory-scope stamp. For a private row the stamp drops `scope_key`. A private row whose owner was recorded only in `scope_key`, with no `principal_id`, therefore comes back with no owner at all, and its own owner can no longer read it.

When a restored private row has no `principal_id`, carry the owner from `scope_key` into `principal_id`. The restored row must have `principal_id` set to that owner, no `scope_key`, and be readable by that owner and nobody else.
