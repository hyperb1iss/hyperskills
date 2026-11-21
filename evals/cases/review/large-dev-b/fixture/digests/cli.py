"""Command line entry points, run by the scheduler (see docs/OPERATIONS.md).

The deployment entry point builds a Context from production services and calls
``main``; tests build one from in-memory stores.
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from .job import DigestJob
from .ledger import DigestLedger
from .mailer import RecordingTransport
from .notify import notify_new_events


@dataclass
class Context:
    users: object
    prefs: object
    events: object
    transport: object
    settings: object
    clock: object = None
    ledger: object = None

    def now(self):
        return self.clock() if self.clock else datetime.now(timezone.utc)

    def digest_ledger(self):
        if self.ledger is None:
            self.ledger = DigestLedger(self.settings.digest_ledger_path)
        return self.ledger


def parse_moment(text):
    """An ISO 8601 timestamp with an explicit offset."""
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO timestamp: {text!r}") from None
    if moment.tzinfo is None:
        raise argparse.ArgumentTypeError(f"timestamp needs an offset: {text!r}")
    return moment


def build_parser():
    parser = argparse.ArgumentParser(prog="digests")
    commands = parser.add_subparsers(dest="command", required=True)
    notify = commands.add_parser("notify", help="email events received in a window")
    notify.add_argument("--since", type=parse_moment, required=True)
    notify.add_argument("--until", type=parse_moment)
    digest = commands.add_parser("digest", help="send the digests due now")
    digest.add_argument("--now", type=parse_moment, help="with --dry-run, show what would be sent at this time")
    digest.add_argument("--dry-run", action="store_true", help="show what would be sent; send and record nothing")
    return parser


def main(argv, context, out=sys.stdout):
    args = build_parser().parse_args(argv)
    if args.command == "notify":
        until = args.until or context.now()
        if until <= args.since:
            print("--until must be after --since", file=out)
            return 2
        report = notify_new_events(
            context.events, context.users, context.prefs, context.transport,
            args.since, until, context.settings.sender,
        )
        print(f"sent={report.sent} skipped={report.skipped}", file=out)
        return 0
    if args.command == "digest":
        if args.now is not None and not args.dry_run:
            print("--now needs --dry-run; a real run always uses the clock", file=out)
            return 2
        now = args.now or context.now()
        transport = RecordingTransport() if args.dry_run else context.transport
        job = DigestJob(
            context.users, context.prefs, context.events, context.digest_ledger(),
            transport, context.settings, record=not args.dry_run,
        )
        report = job.run(now)
        print(report.summary(), file=out)
        if args.dry_run:
            for message in transport.sent:
                print(f"would send to {message.to}: {message.subject}", file=out)
        return 0
    return 2
