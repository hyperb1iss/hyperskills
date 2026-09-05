#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Regenerate marked documentation from validated skills and Git-visible files."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from validate_skills import validate


def replace_region(text: str, name: str, body: str) -> str:
    """Replace one explicitly marked region, preserving all surrounding bytes."""
    start = f"<!-- BEGIN GENERATED: {name} -->"
    end = f"<!-- END GENERATED: {name} -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one marker pair for {name}")
    before, rest = text.split(start)
    middle, after = rest.split(end) if end in rest else (None, None)
    if middle is None or "<!-- BEGIN GENERATED:" in middle:
        raise ValueError(f"reversed or nested markers for {name}")
    return before + start + "\n\n" + body.rstrip() + "\n\n" + end + after


def source_files(root: Path) -> list[str]:
    """Include tracked and new source, excluding ignored build and local artifacts."""
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    files = sorted(set(raw.decode("utf-8").rstrip("\0").split("\0")))
    result = []
    for name in files:
        if not name:
            continue
        if any(character in name for character in "\n\r\t`"):
            raise ValueError(f"filename cannot be represented in the tree: {name!r}")
        path = root / name
        if path.is_file() or path.is_symlink():
            result.append(name)
    return result


def render_tree(files: list[str]) -> str:
    tree: dict = {}
    for name in files:
        node = tree
        for part in name.split("/"):
            node = node.setdefault(part, {})
    lines = ["```text", "hyperskills/"]

    def visit(node: dict, prefix: str) -> None:
        for index, (name, children) in enumerate(sorted(node.items())):
            last = index == len(node) - 1
            lines.append(
                prefix + ("└── " if last else "├── ") + name + ("/" if children else "")
            )
            visit(children, prefix + ("    " if last else "│   "))

    visit(tree, "")
    return "\n".join([*lines, "```"])


def render_inventory(root: Path, files: list[str]) -> str:
    rows = []
    for directory in sorted((root / "skills").iterdir()):
        if directory.is_dir():
            references = sum(
                name.startswith(f"skills/{directory.name}/references/")
                for name in files
            )
            rows.append(
                [
                    f"[{directory.name}](skills/{directory.name}/SKILL.md)",
                    str(references),
                ]
            )
    headers = ["Skill", "Reference files"]
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(2)]

    def row_text(row: list[str]) -> str:
        return (
            "| "
            + " | ".join(
                value.ljust(width) for value, width in zip(row, widths, strict=True)
            )
            + " |"
        )

    return "\n".join(
        [
            row_text(headers),
            row_text(["-" * width for width in widths]),
            *(row_text(row) for row in rows),
        ]
    )


def marketplace_update(root: Path) -> tuple[str, str] | None:
    """Copy the canonical description without changing other marketplace values."""
    plugin = json.loads(
        (root / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    description = plugin.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("plugin description must be a nonempty string")
    filename = ".claude-plugin/marketplace.json"
    path = root / filename
    if path.is_symlink():
        raise ValueError(f"generated document must not be a symlink: {filename}")
    marketplace = json.loads(path.read_text(encoding="utf-8"))
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or any(
        not isinstance(entry, dict) for entry in entries
    ):
        raise ValueError("marketplace plugins must be a list of objects")
    matches = [entry for entry in entries if entry.get("name") == plugin["name"]]
    if len(matches) != 1:
        raise ValueError("marketplace must contain exactly one matching plugin entry")
    if matches[0].get("description") == description:
        return None
    matches[0]["description"] = description
    return filename, json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"


def synchronize(root: Path, check: bool = False) -> list[str]:
    """Validate and render every output before writing; return changed filenames."""
    count, errors = validate(root)
    if errors:
        raise ValueError("\n".join(errors))
    files = source_files(root)
    directories = sorted(path for path in (root / "skills").iterdir() if path.is_dir())
    for directory in directories:
        if f"skills/{directory.name}/SKILL.md" not in files:
            raise ValueError(f"skill entrypoint is ignored by Git: {directory.name}")
    badge = (
        '<p align="center">\n'
        f'  <img src="https://img.shields.io/badge/Skills-{count}-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="{count} Skills">\n'
        "</p>"
    )
    replacements = {
        "AGENTS.md": {
            "repository-map": render_tree(files),
            "skill-inventory": render_inventory(root, files),
        },
        "README.md": {"skill-badge": badge},
    }
    updates = {}
    marketplace = marketplace_update(root)
    if marketplace is not None:
        updates[marketplace[0]] = marketplace[1]
    for filename, regions in replacements.items():
        path = root / filename
        if path.is_symlink():
            raise ValueError(f"generated document must not be a symlink: {filename}")
        original = path.read_bytes().decode("utf-8")
        rendered = original
        for name, body in regions.items():
            rendered = replace_region(rendered, name, body)
        if rendered != original:
            updates[filename] = rendered
    if not check:
        for filename, content in updates.items():
            (root / filename).write_bytes(content.encode("utf-8"))
    return list(updates)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--check", action="store_true", help="report drift without changing files"
    )
    args = parser.parse_args()
    try:
        changed = synchronize(args.root, args.check)
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Metadata generation failed: {error}")
        return 1
    if changed:
        print(("Metadata drift: " if args.check else "Updated: ") + ", ".join(changed))
    else:
        print("Generated metadata is current")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
