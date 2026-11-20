Handoff: tallyhouse ghost rows (for Dagny)

Root cause = H1, retry after commit when the ack times out -> confirmed on staging w/ the 6 s delay; H2 out; H3 out as a cause but mind T7. Fix A stays reverted (see Tue rollback); fix B = PR 4471 -> flag on in staging, off in prod; 18 h soak clean, zero new ghost rows.

Left for you: (1) flip the flag in prod Thursday after T7; (2) the sweep: written, dry-run on staging only; do NOT run in prod w/o Corwin's OK, it moves Nov invoiced totals (412 accounts, ~0.8% of billed units); (3) order: prod dry run -> `tallyctl sweep --dry-run --month 2026-11` -> diff vs DUR, should match within rounding -> Corwin -> real run. Asked Corwin Wed, no reply; chase if quiet by Thu noon.

Also: the 6 s ack delay is still on ingest-2 for repro, pull it before Fri's staging release. Fix A can come back later, not urgent; fix B covers it. Everything else is in my log.
