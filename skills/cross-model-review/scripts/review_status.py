#!/usr/bin/env python3
"""Print a concise snapshot for an observable Claude review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def display(value: Any) -> str:
    return "-" if value is None else str(value)


def main() -> int:
    args = parse_arguments()
    status_path = args.review_dir.resolve() / "status.json"
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"status file not found: {status_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"invalid status file {status_path}: {error}", file=sys.stderr)
        return 2

    if not isinstance(status, dict):
        print(f"invalid status file {status_path}: expected an object", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0

    print(f"state={display(status.get('state'))}")
    print(f"phase={display(status.get('phase'))}")
    if "scope" in status:
        print(
            f"scope={json.dumps(status['scope']) if status['scope'] else 'whole-worktree'}"
        )
    if "auth_mode" in status:
        print(f"auth_mode={status['auth_mode']}")
    print(f"activity={display(status.get('last_activity'))}")
    print(f"last_event_at={display(status.get('last_event_at'))}")
    print(f"event_count={display(status.get('event_count'))}")
    if "target_stale" in status:
        target_stale = status["target_stale"]
        value = "unknown" if target_stale is None else str(bool(target_stale)).lower()
        print(f"target_stale={value}")
    if status.get("final_file"):
        print(f"final_file={status['final_file']}")
    if status.get("error"):
        print(f"error={status['error']}")
    if status.get("freshness_error"):
        print(f"freshness_error={status['freshness_error']}")
    if status.get("wrapper_exit_code") is not None:
        print(f"wrapper_exit_code={status['wrapper_exit_code']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
