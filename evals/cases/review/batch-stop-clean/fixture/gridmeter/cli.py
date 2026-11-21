"""gridmeter command line."""
import argparse
import sys

from .importer import import_file
from .store import ReadingStore


def main(argv=None, store=None, out=sys.stdout):
    parser = argparse.ArgumentParser(prog="gridmeter")
    commands = parser.add_subparsers(dest="command", required=True)
    load = commands.add_parser("import", help="import vendor CSV drops")
    load.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    store = store if store is not None else ReadingStore()
    status = 0
    for path in args.paths:
        summary = import_file(path, store)
        print(f"{path}: imported {summary.imported}, rejected {len(summary.rejected)}", file=out)
        for problem in summary.rejected:
            print(f"  {problem}", file=out)
        if summary.rejected:
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
