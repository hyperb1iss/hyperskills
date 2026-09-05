#!/usr/bin/env python3
"""Run an observable, read-only Claude review and persist its event stream."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ALLOWED_TOOLS = "Read,Glob,Grep"
DISALLOWED_TOOLS = "Write,Edit,MultiEdit,NotebookEdit,Bash,mcp__*"
STRIPPED_AUTH_VARIABLES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
STALE_EXIT_CODE = 90
REVIEW_FAILED_EXIT_CODE = 91


class TerminationRequested(Exception):
    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"received signal {signum}")


def request_termination(signum: int, _frame: Any) -> None:
    raise TerminationRequested(signum)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def run_git(cwd: Path, *arguments: str) -> bytes | None:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def git_worktree_root(cwd: Path) -> Path | None:
    root = run_git(cwd, "rev-parse", "--show-toplevel")
    if root is None:
        return None
    return Path(os.fsdecode(root.rstrip(b"\n"))).resolve()


def normalize_scope(values: list[str], root: Path) -> list[str]:
    """Accept literal repository-relative paths, including deleted files."""
    scopes = set()
    for value in values:
        path = Path(value)
        if not value or path.is_absolute() or ".." in path.parts:
            raise ValueError(f"scope must be a repository-relative path: {value!r}")
        candidate = root / path
        if not candidate.resolve().is_relative_to(root):
            raise ValueError(f"scope escapes the reviewed worktree: {value!r}")
        if path.parts and path.parts[0] == ".git":
            raise ValueError("scope cannot include Git metadata")
        scopes.add(path.as_posix())
    return sorted(scopes)


def git_snapshot(cwd: Path, scope: list[str] | None = None) -> dict[str, Any]:
    """Compare net endpoint state; this is neither atomic nor a read sandbox.

    Ignored files, external dependencies, and edits reverted between snapshots
    are outside this check. Keep a scoped review's actual reads within its brief.
    """
    scope = scope or []
    worktree_root = git_worktree_root(cwd)
    if worktree_root is None:
        return {"available": False, "reason": "git-unavailable"}
    try:
        normalize_scope(scope, worktree_root)
    except ValueError:
        return {"available": False, "reason": "scope-escaped"}
    paths = ["--", *(f":(literal){path}" for path in scope)]
    head = run_git(worktree_root, "rev-parse", "HEAD")
    # Separate index and worktree deltas: diff HEAD alone misses index-only
    # edits when the worktree remains unchanged and status stays MM.
    parts = [
        run_git(worktree_root, "status", "--porcelain=v1", "-z", *paths),
        run_git(
            worktree_root,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--binary",
            "--cached",
            "HEAD",
            *paths,
        ),
        run_git(
            worktree_root, "diff", "--no-ext-diff", "--no-textconv", "--binary", *paths
        ),
        run_git(worktree_root, "ls-tree", "-r", "-z", "HEAD", *paths),
    ]
    untracked = run_git(
        worktree_root, "ls-files", "--others", "--exclude-standard", "-z", *paths
    )
    if head is None or any(part is None for part in parts) or untracked is None:
        return {"available": False, "reason": "git-unavailable"}

    digest = hashlib.sha256()
    # A narrow review should survive unrelated commits. Its selected base tree
    # above still detects committed changes within scope.
    if not scope:
        parts.insert(0, head)
    for part in parts:
        assert part is not None
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    for raw_path in untracked.split(b"\0"):
        if not raw_path:
            continue
        digest.update(b"\0untracked\0")
        digest.update(len(raw_path).to_bytes(8, "big"))
        digest.update(raw_path)
        path = worktree_root / os.fsdecode(raw_path)
        try:
            content_digest = hashlib.sha256()
            if path.is_symlink():
                content_digest.update(b"symlink\0" + os.fsencode(os.readlink(path)))
            elif path.is_file():
                content_digest.update(b"file\0")
                with path.open("rb") as untracked_file:
                    for chunk in iter(lambda: untracked_file.read(1024 * 1024), b""):
                        content_digest.update(chunk)
            else:
                content_digest.update(b"<not-a-regular-file>")
            digest.update(content_digest.digest())
        except OSError:
            return {"available": False, "reason": "untracked-io-error"}
    return {
        "available": True,
        "head": head.decode().strip(),
        "scope": scope,
        "worktree_root": str(worktree_root),
        "worktree_fingerprint": digest.hexdigest(),
    }


def normalized_path(value: Any, cwd: Path) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return str((cwd / value).resolve().relative_to(cwd.resolve()))
    except ValueError:
        return value


def tool_activity(block: dict[str, Any], cwd: Path) -> tuple[str, str]:
    name = str(block.get("name", "tool"))
    tool_input = block.get("input")
    if not isinstance(tool_input, dict):
        return "inspecting", name

    path = normalized_path(tool_input.get("file_path") or tool_input.get("path"), cwd)
    if path:
        return "inspecting", f"{name} {path}"

    pattern = tool_input.get("pattern")
    if isinstance(pattern, str) and pattern:
        return "inspecting", f"{name} pattern={pattern[:120]}"

    command = tool_input.get("command")
    if isinstance(command, str) and command:
        summary = " ".join(command.split())[:160]
        return "validating", f"{name} {summary}"

    return "inspecting", name


def activity_from_event(event: dict[str, Any], cwd: Path) -> tuple[str, str] | None:
    event_type = event.get("type")
    if event_type == "system" and event.get("subtype") == "init":
        return "starting", "Claude initialized"
    if event_type == "system" and event.get("subtype") == "permission_denied":
        tool = event.get("tool_name", "tool")
        return "validating", f"Claude permission denied for {tool}"
    if event_type != "assistant":
        return None

    message = event.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if not isinstance(content, list):
        return None

    for block in reversed(content):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use":
            return tool_activity(block, cwd)
        if block.get("type") == "text" and block.get("text"):
            return "reporting", "Claude produced review text"
    return None


def terminate_process_tree(
    process: subprocess.Popen[str], grace_seconds: float = 5
) -> None:
    """Terminate our session's group even when its leader already exited."""
    if os.name != "posix":
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
        process.wait()
        return

    def signal_group(signum: int) -> bool:
        try:
            os.killpg(process.pid, signum)
            return True
        except ProcessLookupError:
            return False

    signal_group(signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        process.poll()  # Reap the leader so its zombie cannot keep the group alive.
        if not signal_group(0):
            break
        time.sleep(0.02)
    else:
        signal_group(signal.SIGKILL)
    process.wait()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--label", default="review")
    parser.add_argument("--review-dir", type=Path)
    parser.add_argument("--claude-bin", default=shutil.which("claude") or "claude")
    parser.add_argument(
        "--auth-mode",
        choices=("inherit", "subscription"),
        default="inherit",
        help="inherit the caller's auth route; subscription removes child API key/token overrides",
    )
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        metavar="PATH",
        help="literal repository-relative file/directory to fingerprint (repeatable)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    cwd = args.cwd.resolve()
    prompt_file = args.prompt_file.resolve()
    if not cwd.is_dir():
        raise SystemExit(f"review cwd is not a directory: {cwd}")
    if not prompt_file.is_file():
        raise SystemExit(f"prompt file does not exist: {prompt_file}")
    if prompt_file.stat().st_size == 0:
        raise SystemExit(f"prompt file is empty: {prompt_file}")

    safe_label = re.sub(r"[^A-Za-z0-9._-]", "-", args.label)
    git_root = git_worktree_root(cwd)
    reviewed_root = git_root or cwd
    if args.scope and git_root is None:
        raise SystemExit("--scope requires a Git worktree")
    try:
        scope = normalize_scope(args.scope, reviewed_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    review_dir = (
        args.review_dir.resolve()
        if args.review_dir
        else Path(tempfile.mkdtemp(prefix=f"claude-review-{safe_label}-")).resolve()
    )
    if review_dir == reviewed_root or reviewed_root in review_dir.parents:
        raise SystemExit(
            f"review directory must live outside the reviewed worktree: {review_dir}"
        )
    if review_dir.exists():
        if not review_dir.is_dir():
            raise SystemExit(f"review directory is not a directory: {review_dir}")
        if any(review_dir.iterdir()):
            raise SystemExit(f"review directory is not empty: {review_dir}")
    review_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(review_dir, 0o700)
    events_path = review_dir / "events.jsonl"
    stderr_path = review_dir / "stderr.log"
    final_path = review_dir / "final.md"
    status_path = review_dir / "status.json"
    started_at = utc_now()
    status: dict[str, Any] = {
        "event_count": 0,
        "last_activity": "Preparing Claude review",
        "last_event_at": None,
        "phase": "starting",
        "review_dir": str(review_dir),
        "started_at": started_at,
        "state": "starting",
        "target_sha": None,
        "scope": scope,
        "auth_mode": args.auth_mode,
    }
    atomic_json(status_path, status)

    print(f"review_dir={review_dir}", flush=True)
    print(f"status_file={status_path}", flush=True)
    print(f"events_file={events_path}", flush=True)

    handled_signals = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
        handled_signals.append(signal.SIGHUP)
    previous_handlers = {
        signum: signal.signal(signum, request_termination) for signum in handled_signals
    }
    process: subprocess.Popen[str] | None = None
    try:
        copied_prompt = review_dir / "prompt.md"
        prompt_bytes = prompt_file.read_bytes()
        if not prompt_bytes:
            raise ValueError("prompt file became empty before capture")
        copied_prompt.write_bytes(prompt_bytes)
        copied_prompt.chmod(0o400)
        metadata = {
            "allowed_tools": ALLOWED_TOOLS,
            "auth_mode": args.auth_mode,
            "cwd": str(cwd),
            "label": args.label,
            "prompt_source": str(prompt_file),
            "prompt_file": str(copied_prompt),
            "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
            "scope": scope,
            "started_at": started_at,
        }
        atomic_json(review_dir / "meta.json", metadata)
        status["last_activity"] = "Capturing the initial Git target"
        atomic_json(status_path, status)
        initial_snapshot = git_snapshot(cwd, scope)
        metadata["initial_git"] = initial_snapshot
        atomic_json(review_dir / "meta.json", metadata)
        status["target_sha"] = initial_snapshot.get("head")
        atomic_json(status_path, status)

        environment = os.environ.copy()
        if args.auth_mode == "subscription":
            for variable in STRIPPED_AUTH_VARIABLES:
                environment.pop(variable, None)
        command = [
            args.claude_bin,
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--no-session-persistence",
            "--safe-mode",
            "--permission-mode",
            "dontAsk",
            "--tools",
            ALLOWED_TOOLS,
            "--allowedTools",
            ALLOWED_TOOLS,
            "--disallowedTools",
            DISALLOWED_TOOLS,
        ]
        result_event: dict[str, Any] | None = None
        with (
            events_path.open(
                "a", encoding="utf-8", errors="replace", buffering=1
            ) as events_file,
            stderr_path.open(
                "a", encoding="utf-8", errors="replace", buffering=1
            ) as stderr_file,
        ):
            try:
                pending_signals: list[int] = []

                def defer_termination(signum: int, _frame: Any) -> None:
                    pending_signals.append(signum)

                spawn_handlers = {
                    signum: signal.signal(signum, defer_termination)
                    for signum in handled_signals
                }
                try:
                    with copied_prompt.open(
                        "r", encoding="utf-8", errors="replace"
                    ) as prompt:
                        process = subprocess.Popen(
                            command,
                            cwd=cwd,
                            env=environment,
                            stdin=prompt,
                            stdout=subprocess.PIPE,
                            stderr=stderr_file,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            bufsize=1,
                            start_new_session=os.name == "posix",
                        )
                finally:
                    for signum, spawn_handler in spawn_handlers.items():
                        signal.signal(signum, spawn_handler)
                if pending_signals:
                    raise TerminationRequested(pending_signals[0])
            except OSError as error:
                status.update(
                    {
                        "completed_at": utc_now(),
                        "error": str(error),
                        "final_file": None,
                        "last_activity": "Claude failed to start",
                        "phase": "failed",
                        "state": "failed",
                        "target_stale": None,
                        "wrapper_exit_code": 127,
                    }
                )
                atomic_json(status_path, status)
                return 127

            metadata["pid"] = process.pid
            atomic_json(review_dir / "meta.json", metadata)
            status.update({"pid": process.pid, "state": "running"})
            atomic_json(status_path, status)

            assert process.stdout is not None
            for line in process.stdout:
                events_file.write(line)
                events_file.flush()
                status["event_count"] += 1
                status["last_event_at"] = utc_now()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    status.update(
                        {
                            "last_activity": "Claude emitted a non-JSON event",
                            "phase": "running",
                        }
                    )
                else:
                    if not isinstance(event, dict):
                        atomic_json(status_path, status)
                        continue
                    activity = activity_from_event(event, cwd)
                    if activity:
                        status["phase"], status["last_activity"] = activity
                    if event.get("type") == "result":
                        result_event = event
                        status.update(
                            {
                                "last_activity": "Claude emitted its final result",
                                "phase": "reporting",
                            }
                        )
                atomic_json(status_path, status)

            exit_code = process.wait()
            terminate_process_tree(process)
        status.update(
            {
                "phase": "finalizing",
                "last_activity": "Capturing the final Git target",
            }
        )
        atomic_json(status_path, status)
        final_snapshot = git_snapshot(cwd, scope)
        initial_freshness = bool(initial_snapshot.get("available"))
        final_freshness = bool(final_snapshot.get("available"))
        if initial_freshness and final_freshness:
            target_stale: bool | None = any(
                initial_snapshot.get(key) != final_snapshot.get(key)
                for key in ("worktree_root", "scope", "worktree_fingerprint")
            )
        elif initial_freshness:
            target_stale = True
        else:
            target_stale = None
        result_text = result_event.get("result") if result_event else None
        result_error = bool(result_event and result_event.get("is_error"))
        result_subtype = result_event.get("subtype") if result_event else None
        completed = (
            exit_code == 0
            and result_event is not None
            and not result_error
            and result_subtype == "success"
            and isinstance(result_text, str)
            and bool(result_text.strip())
        )
        if completed:
            final_path.write_text(result_text.rstrip() + "\n", encoding="utf-8")

        state = (
            "stale"
            if completed and target_stale is True
            else "complete"
            if completed
            else "failed"
        )
        if state == "stale":
            wrapper_exit_code = STALE_EXIT_CODE
        elif not completed:
            wrapper_exit_code = REVIEW_FAILED_EXIT_CODE
        else:
            wrapper_exit_code = 0
        failure_reason = None
        if not completed:
            if exit_code != 0:
                failure_reason = f"Claude exited with code {exit_code}"
            elif result_event is None:
                failure_reason = "Claude emitted no result event"
            elif result_error:
                failure_reason = "Claude emitted an error result"
            elif result_subtype != "success":
                failure_reason = f"Claude result subtype was {result_subtype!r}"
            else:
                failure_reason = "Claude emitted an empty result"
        status.update(
            {
                "completed_at": utc_now(),
                "exit_code": exit_code,
                "final_file": str(final_path) if final_path.exists() else None,
                "final_git": final_snapshot,
                "freshness_error": (
                    final_snapshot.get("reason")
                    if initial_freshness and not final_freshness
                    else initial_snapshot.get("reason")
                    if not initial_freshness
                    else None
                ),
                "last_activity": (
                    "Reviewed target changed while Claude was running"
                    if state == "stale"
                    else "Claude report complete; reviewer approval is not inferred"
                    if completed
                    else "Claude review failed"
                ),
                "phase": state,
                "result_subtype": result_subtype,
                "state": state,
                "target_stale": target_stale,
                "wrapper_exit_code": wrapper_exit_code,
            }
        )
        if failure_reason:
            status["error"] = failure_reason
        atomic_json(status_path, status)
        print(f"claude_exit={exit_code}", flush=True)
        print(f"review_state={state}", flush=True)
        print(f"final_file={final_path if final_path.exists() else ''}", flush=True)
        return wrapper_exit_code

    except BaseException as error:
        # Repeated cancellation must not interrupt cleanup or terminal status.
        for signum in handled_signals:
            signal.signal(signum, signal.SIG_IGN)
        if process is not None:
            terminate_process_tree(process)
        if isinstance(error, TerminationRequested):
            wrapper_exit_code = 128 + error.signum
        elif isinstance(error, KeyboardInterrupt):
            wrapper_exit_code = 130
        else:
            wrapper_exit_code = 1
        status.update(
            {
                "completed_at": utc_now(),
                "error": f"{type(error).__name__}: {error}",
                "exit_code": process.returncode if process else None,
                "final_file": None,
                "last_activity": "Observable review runner interrupted",
                "phase": "failed",
                "state": "failed",
                "target_stale": None,
                "wrapper_exit_code": wrapper_exit_code,
            }
        )
        atomic_json(status_path, status)
        if isinstance(error, (TerminationRequested, KeyboardInterrupt)):
            return wrapper_exit_code
        raise
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


if __name__ == "__main__":
    sys.exit(main())
