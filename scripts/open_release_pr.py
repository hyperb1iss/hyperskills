#!/usr/bin/env python3
"""Commit a prepared release, reuse matching remote work, and request its CI."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RELEASE_FILES = (".claude-plugin/plugin.json", "CHANGELOG.md", "release.json")


def run(*args: str, input: str | None = None) -> str:
    return subprocess.run(
        args, input=input, text=True, capture_output=True, check=True
    ).stdout.rstrip("\n")


def open_pr(repo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("repository must be OWNER/REPO")
    run(sys.executable, str(Path(__file__).with_name("release.py")), "check")
    record = json.loads(Path("release.json").read_text(encoding="utf-8"))
    version, source = record["version"], record["source_commit"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or not re.fullmatch(
        r"[0-9a-f]{40}", source
    ):
        raise ValueError("invalid release identity")
    if run("git", "rev-parse", "HEAD") != source:
        raise ValueError("open from the checkout used to prepare this release")
    changed = set(
        filter(
            None,
            (
                run("git", "diff", "--name-only", "-z", "HEAD")
                + run("git", "diff", "--cached", "--name-only", "-z")
                + run("git", "ls-files", "--others", "--exclude-standard", "-z")
            ).split("\0"),
        )
    )
    if changed - set(RELEASE_FILES):
        raise ValueError("unrelated edits present; only release files may be committed")
    for path in RELEASE_FILES:
        staged = run("git", "ls-files", "--stage", "--", path).splitlines()
        base = run("git", "ls-tree", "HEAD", "--", path).split()
        if not staged:
            if base:
                raise ValueError(f"conflicting staged release deletion: {path}")
            continue
        fields = staged[0].split()
        generated = run("git", "hash-object", "--", path)
        allowed = {generated}
        if base:
            allowed.add(base[2])
        if (
            len(staged) != 1
            or fields[2] != "0"
            or fields[0] != (base[0] if base else "100644")
            or fields[1] not in allowed
        ):
            raise ValueError(f"conflicting staged release content: {path}")
    run("git", "add", "--", *RELEASE_FILES)
    tree = run("git", "write-tree")
    branch = f"release/v{version}-{source[:12]}"
    remote = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            f"refs/heads/{branch}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if remote.returncode == 0:
        run("git", "fetch", "origin", f"refs/heads/{branch}")
        if (
            run("git", "rev-parse", "FETCH_HEAD^{tree}") != tree
            or run("git", "rev-parse", "FETCH_HEAD^") != source
        ):
            raise ValueError(
                "existing release branch differs; refusing to overwrite it"
            )
    elif remote.returncode == 2:
        run(
            "git",
            "commit",
            "-F",
            "-",
            input=f"chore(release): prepare v{version}\n\n"
            "Record the selected version and release notes together.\n"
            "Publishing validates this commit before creating its release.\n",
        )
        run("git", "push", "origin", f"HEAD:refs/heads/{branch}")
    else:
        raise RuntimeError(
            f"cannot inspect remote release branch: {remote.stderr.strip()}"
        )
    prs = json.loads(
        run(
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            branch,
            "--base",
            "main",
            "--state",
            "all",
            "--json",
            "url,state",
        )
    )
    if prs:
        if len(prs) != 1 or prs[0]["state"] != "OPEN":
            raise ValueError("release branch already has a closed or ambiguous PR")
        url = prs[0]["url"]
    else:
        body = (
            f"Release version {version}. The version, changelog, and captured notes "
            "are prepared together from the source commit "
            f"`{source}`.\n\n{record['notes']}\n\n"
            "## 🧪 Validation\n\n"
            "The preparation workflow validates the source and generated metadata. "
            "CI checks the release branch separately. Merging publishes the exact "
            "merged commit after its checks pass. If main advances, prepare a new "
            "release PR from that revision before merging.\n"
        )
        url = run(
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            f"chore(release): v{version}",
            "--body-file",
            "-",
            input=body,
        )
    # Bot pushes do not start ordinary push workflows. Dispatch CI explicitly.
    run(
        "gh",
        "api",
        f"repos/{repo}/actions/workflows/ci.yml/dispatches",
        "--method",
        "POST",
        "--input",
        "-",
        input=json.dumps({"ref": branch}),
    )
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    try:
        print(open_pr(args.repo))
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Release PR failed: {error}")
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip())
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
