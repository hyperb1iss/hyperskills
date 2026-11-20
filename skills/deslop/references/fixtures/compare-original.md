---
title: Compare Fixture
---

<!-- markdownlint-disable MD034 -->

## Cache warmup

The warmup job may reduce cold-start latency by roughly 40% on a 2-4 node cluster, according to Smith et al., 2024. Results could vary with cache size [3].

Run `make warm` before a deploy, and pass `--nodes 4` when the cluster is larger than the default.

```sh
make warm --nodes 4
```

> Warm caches never guarantee a fast first request.

See the [runbook](https://x.test/runbook) and https://x.test/metrics for the measurements.
