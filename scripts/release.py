#!/usr/bin/env python3
"""Prepare explicit releases and publish their exact, verified Git commits."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = ".claude-plugin/plugin.json"
RECORD = "release.json"
CHANGELOG = "CHANGELOG.md"
SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


class ReleaseError(Exception):
    """A release precondition failed without authorizing recovery mutations."""


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ReleaseError(result.stderr.strip())
    return result.stdout.rstrip("\n")


def at(commit: str, path: str) -> str | None:
    # Probe the tree first: a missing path is normal, but a broken Git read is not.
    listing = git("ls-tree", commit, "--", path)
    if not listing:
        return None
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ReleaseError(result.stderr.strip())
    return result.stdout


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def bump_version(version: str, bump: str) -> str:
    match = SEMVER.fullmatch(version)
    if not match:
        raise ReleaseError(f"Not a stable semantic version: {version!r}")
    numbers = list(map(int, match.groups()))
    index = {"major": 0, "minor": 1, "patch": 2}[bump]
    numbers[index] += 1
    numbers[index + 1 :] = [0] * (2 - index)
    return ".".join(map(str, numbers))


def expected(record: dict) -> dict[str, str]:
    required = {"version", "previous_version", "source_commit", "notes", "bump"}
    if set(record) != required or not all(isinstance(v, str) for v in record.values()):
        raise ReleaseError(
            "release.json must contain exactly the release schema fields"
        )
    if record["bump"] not in {"patch", "minor", "major"}:
        raise ReleaseError("Invalid release increment")
    if not re.fullmatch(r"[0-9a-f]{40}", record["source_commit"]):
        raise ReleaseError("The release source must be a full Git commit SHA")
    if not record["notes"].strip() or record["notes"] != record["notes"].strip() + "\n":
        raise ReleaseError("Release notes must be nonempty and normalized")
    source = record["source_commit"]
    raw = at(source, MANIFEST)
    if raw is None:
        raise ReleaseError("Source commit has no plugin manifest")
    manifest = json.loads(raw)
    if manifest["version"] != record["previous_version"]:
        raise ReleaseError("Previous version differs from the source commit")
    if bump_version(manifest["version"], record["bump"]) != record["version"]:
        raise ReleaseError("Release version does not match the requested increment")
    manifest["version"] = record["version"]
    previous = at(source, CHANGELOG) or "# Changelog\n"
    if not previous.startswith("# Changelog\n"):
        raise ReleaseError("CHANGELOG.md must start with # Changelog")
    changelog = (
        f"# Changelog\n\n## {record['version']}\n\n{record['notes']}"
        + previous[len("# Changelog\n") :]
    )
    return {
        MANIFEST: json_text(manifest),
        RECORD: json_text(record),
        CHANGELOG: changelog,
    }


def dirty_paths() -> set[str]:
    # NUL-delimited output preserves whitespace and Unicode filenames.
    tracked = (git("diff", "--name-only", "-z", "HEAD") or "") + (
        git("diff", "--cached", "--name-only", "-z") or ""
    )
    untracked = git("ls-files", "--others", "--exclude-standard", "-z") or ""
    return set(filter(None, (tracked + untracked).split("\0")))


def read_record() -> dict | None:
    value = json.loads(Path(RECORD).read_text())
    if value is not None and not isinstance(value, dict):
        raise ReleaseError("release.json must be an object")
    return value


def prepare(bump: str, notes_file: str) -> None:
    notes = Path(notes_file).read_text().strip() + "\n"
    if not notes.strip():
        raise ReleaseError("Release notes cannot be empty")
    head = git("rev-parse", "HEAD")
    dirty = dirty_paths()
    if dirty:
        if not Path(RECORD).exists():
            raise ReleaseError("Prepare requires a clean checkout")
        record = read_record()
        if record is None:
            raise ReleaseError("Prepare requires a clean checkout")
        files = expected(record)
        if (
            record["source_commit"] != head
            or record["bump"] != bump
            or record["notes"] != notes
        ):
            raise ReleaseError("A different release or unrelated edits are pending")
        if dirty - set(files) or any(
            Path(p).read_text() != text for p, text in files.items()
        ):
            raise ReleaseError(
                "Pending files differ from the requested release; preserve and resolve edits"
            )
        print(record["version"])
        return
    raw = at(head, MANIFEST)
    if raw is None:
        raise ReleaseError("No plugin manifest at HEAD")
    version = json.loads(raw)["version"]
    record = {
        "version": bump_version(version, bump),
        "previous_version": version,
        "source_commit": head,
        "notes": notes,
        "bump": bump,
    }
    for path, content in expected(record).items():
        Path(path).write_text(content)
    print(record["version"])


def record_at(commit: str) -> dict | None:
    raw = at(commit, RECORD)
    return json.loads(raw) if raw is not None else None


def candidate() -> bool:
    head = git("rev-parse", "HEAD")
    parents = (git("rev-list", "--parents", "-n", "1", "HEAD") or "").split()[1:]
    return record_at(head) != (record_at(parents[0]) if parents else None)


def check() -> dict | None:
    record = read_record() if Path(RECORD).exists() else None
    if record is None:
        if record_at(git("rev-parse", "HEAD")) is not None or candidate():
            raise ReleaseError("Tracked release record was removed")
        return None
    files = expected(record)
    # Skill and manifest prose may evolve after a release. Validate historical
    # release artifacts at the introducing commit, and version continuity now.
    source = record["source_commit"]
    git("merge-base", "--is-ancestor", source, "HEAD")
    if json.loads(Path(MANIFEST).read_text())["version"] != record["version"]:
        raise ReleaseError("Plugin version differs from release.json")
    if Path(CHANGELOG).read_text() != files[CHANGELOG]:
        raise ReleaseError("Changelog differs from captured release notes and history")
    if Path(RECORD).read_text() != files[RECORD]:
        raise ReleaseError("Release record is not canonical")
    if (
        source == git("rev-parse", "HEAD")
        and Path(MANIFEST).read_text() != files[MANIFEST]
    ):
        raise ReleaseError("Pending release manifest includes unrelated changes")
    if candidate() and source != git("rev-parse", "HEAD"):
        parents = (git("rev-list", "--parents", "-n", "1", "HEAD") or "").split()[1:]
        if not parents or parents[0] != source:
            raise ReleaseError(
                "Release commit must directly follow its captured source; regenerate the release PR"
            )
        if Path(MANIFEST).read_text() != files[MANIFEST]:
            raise ReleaseError("Release manifest includes unrelated changes")
        changed = set((git("diff", "--name-only", source, "HEAD") or "").splitlines())
        if changed != set(files):
            raise ReleaseError(
                "Release commit must change only version, changelog, and release record"
            )
    return record


def api(
    repo: str, endpoint: str, *, data: dict | None = None, missing: bool = False
) -> dict | None:
    command = ["gh", "api", "--include", f"repos/{repo}/{endpoint}"]
    if data is not None:
        command += ["--method", "POST", "--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(data) if data is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    header, separator, body = result.stdout.partition("\n\n")
    status = re.match(r"HTTP/\S+ (\d{3})", header)
    code = int(status[1]) if status else None
    if code == 404 and missing:
        return None
    if result.returncode or code is None or not 200 <= code < 300 or not separator:
        raise ReleaseError(
            f"GitHub request failed ({code}): {result.stderr.strip() or result.stdout.strip()}"
        )
    return json.loads(body)


def publish(repo: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ReleaseError("Repository must be OWNER/REPO")
    if dirty_paths():
        raise ReleaseError("Publish requires a clean checkout")
    record = check()
    if record is None or not candidate():
        raise ReleaseError("HEAD is not a release transition")
    sha = git("rev-parse", "HEAD")
    tag = "v" + record["version"]
    ref = api(repo, f"git/ref/tags/{tag}", missing=True)
    if ref is None:
        api(repo, "git/refs", data={"ref": "refs/tags/" + tag, "sha": sha})
        ref = api(repo, f"git/ref/tags/{tag}")
    if ref["object"]["type"] != "commit" or ref["object"]["sha"] != sha:
        raise ReleaseError(
            f"Tag {tag} already points elsewhere or is not a lightweight tag"
        )
    release = api(repo, f"releases/tags/{tag}", missing=True)
    desired = {
        "tag_name": tag,
        "name": tag,
        "body": record["notes"],
        "draft": False,
        "prerelease": False,
    }
    if release is None:
        api(repo, "releases", data={**desired, "target_commitish": sha})
        release = api(repo, f"releases/tags/{tag}")
    if any(release.get(key) != value for key, value in desired.items()):
        raise ReleaseError(
            f"Existing release {tag} differs from captured release intent; refusing overwrite"
        )
    print(f"Published {tag} at {sha}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument(
        "--bump", choices=["patch", "minor", "major"], required=True
    )
    prepare_parser.add_argument("--notes-file", required=True)
    commands.add_parser("check")
    commands.add_parser("candidate")
    publish_parser = commands.add_parser("publish")
    publish_parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    try:
        if git("rev-parse", "--show-prefix"):
            raise ReleaseError("Run from the repository root")
        if args.command == "prepare":
            prepare(args.bump, args.notes_file)
        elif args.command == "check":
            check()
        elif args.command == "candidate":
            print(str(candidate()).lower())
        else:
            publish(args.repo)
    except (ReleaseError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Release error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
