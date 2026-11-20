---
title: Compare Fixture
---

<!-- markdownlint-disable MD034 -->

## Cache warmup

The warmup job reduces cold-start latency by 40% on any cluster, ensuring fast deploys. It always helps, and results improve 3x.

Run `make warm` before a deploy, and pass `--nodes 8` when the cluster is larger than the default.

```sh
make warm --nodes 8
```

> Warm caches never guarantee a fast first request.

See the [runbook](https://x.test/runbook) for the measurements.
