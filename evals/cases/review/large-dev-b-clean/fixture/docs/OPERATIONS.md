# Operations

## Scheduler

All scheduled jobs run from one scheduler host. The scheduler never starts a job
while that job's previous run is still going: if a run is still going at the next
tick, the scheduler skips the tick and pages the on-call engineer. Two runs of the
same job therefore never overlap.

Jobs are listed in `deploy/schedule.yaml`, which lives with the deployment config
in its own repository. A new job ships in two steps: its code merges and deploys
first, and the schedule entry that runs it is added to the deployment config
afterwards. A job's code is therefore inert until its entry lands there.
`digests notify` runs every minute with `--since` set to the previous run's
`--until`.

## Data

- Events: the module docstring in `digests/events.py` describes `occurred_at` and
  `received_at` and how far apart they can be.
- Accounts come from the nightly export at 02:00 UTC. There are about 40,000 active
  accounts. `utc_offset_minutes` is the offset in effect when the export ran; the
  profile service applies daylight saving changes to it.
- State files live under `/var/lib/digests` on the scheduler host. The directory is
  backed up hourly and is never shared with another host.

## Mail

- Every outgoing email links to the notification settings page.
- The relay accepts about 50 messages a second from the scheduler host and queues
  anything beyond that instead of refusing it.
- Transports expect `Message.to` to be an address returned by `parse_address`.
