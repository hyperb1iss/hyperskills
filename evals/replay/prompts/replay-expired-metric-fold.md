The CLI's pending-write metrics file used to carry an `expired` counter, since retired in favour of the outcome counters. `read_pending_metrics` drops `expired` from older files while keeping `attempted`, so after an upgrade completed + replayed + dropped + discarded no longer adds up to attempted.

Count a historical `expired` value as `discarded` when reading. The returned metrics should not contain an `expired` key.
