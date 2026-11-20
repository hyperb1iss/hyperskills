# Tidewater queue migration: status

We have moved 1,840 of our 2,300 queues to the new broker cluster. In the migrated set, median publish latency dropped from 38 ms to 11 ms, a 71% reduction, and the old cluster now carries 22% of peak traffic.

To migrate one of the remaining queues, run `tidectl move --queue <name> --verify` from the ops bastion. As the platform lead put it: "Nothing gets deleted from the old cluster until the verify step reports zero drift."

The remaining 460 queues will move in 3 to 4 weeks, after the retry audit.
