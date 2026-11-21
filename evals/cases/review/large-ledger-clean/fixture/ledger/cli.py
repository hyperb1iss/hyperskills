"""Command line: python -m ledger.cli BOOKS.json COMMAND ..."""
import argparse
import sys
from datetime import date

from .balances import format_trial_balance
from .closing import close_period
from .db import Store
from .importer import import_statement
from .migrations import available, migrate


def build_parser():
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("books")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="bring the books file to the current schema")
    load = commands.add_parser("import", help="import a bank statement CSV")
    load.add_argument("statement")
    load.add_argument("--source", required=True, help="the bank feed this statement came from")
    load.add_argument("--bank", required=True)
    load.add_argument("--clearing", required=True)
    close = commands.add_parser("close", help="close the books through a date")
    close.add_argument("end", type=date.fromisoformat)
    show = commands.add_parser("trial-balance")
    show.add_argument("--through", type=date.fromisoformat)
    return parser


def main(argv=None, out=sys.stdout):
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store.load(args.books)
    status = 0
    if args.command == "migrate":
        applied = migrate(store)
        print(f"applied migrations {applied}" if applied else "already current", file=out)
    elif store.schema_version != available()[-1][0]:
        parser.error("these books need migrating first: run the migrate command")
    elif args.command == "import":
        result = import_statement(store, args.statement, args.source, args.bank, args.clearing)
        print(f"posted {len(result.posted)}, skipped {len(result.skipped)}, rejected {len(result.rejected)}",
              file=out)
        for problem in result.rejected:
            print(f"  {problem}", file=out)
        status = 1 if result.rejected else 0
    elif args.command == "close":
        close_period(store, args.end)
        print(f"closed through {args.end}", file=out)
    else:
        print(format_trial_balance(store, args.through), file=out)
    store.save(args.books)
    return status


if __name__ == "__main__":
    sys.exit(main())
