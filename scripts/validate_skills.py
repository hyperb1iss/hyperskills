#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Validate the plugin and skill metadata without executing skill content."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?",
    re.ASCII,
)


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently accepting the last value."""

    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if any(not isinstance(key, str) for key in keys):
            raise ValueError("frontmatter keys must be strings")
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate frontmatter key")
        return super().construct_mapping(node, deep=deep)


def validate_skill(directory: Path) -> list[str]:
    """Check frontmatter and concrete bundled-resource references in an entrypoint."""
    path = directory / "SKILL.md"
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            raise ValueError("missing opening frontmatter delimiter")
        try:
            closing = lines.index("---", 1)
        except ValueError:
            raise ValueError("missing closing frontmatter delimiter") from None
        metadata = yaml.load("\n".join(lines[1:closing]), Loader=UniqueKeyLoader)
        if not isinstance(metadata, dict):
            raise TypeError("frontmatter must be a mapping")
        name = metadata.get("name")
        if (
            not isinstance(name, str)
            or len(name) > 64
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or name != directory.name
        ):
            errors.append(
                "name must match its directory and use lowercase hyphenated words"
            )
        description = metadata.get("description")
        if (
            not isinstance(description, str)
            or not 1 <= len(description.strip()) <= 1024
        ):
            errors.append(
                "description must be a nonempty string of at most 1024 characters"
            )
        body = "\n".join(lines[closing + 1 :])
        if not body.strip():
            errors.append("skill body is empty")
        if len(body.split()) >= 5000:
            errors.append("entrypoint exceeds the repository's 5000-word ceiling")
        # This checks concrete resource declarations, not arbitrary example paths or URLs.
        for reference in sorted(
            set(
                re.findall(
                    r"(?:`|\()((?:references|scripts|assets)/[^`\s)]+)(?:`|\))", body
                )
            )
        ):
            if any(marker in reference for marker in ("<", ">", "*", "...")):
                continue
            target = (directory / reference.split("#", 1)[0]).resolve()
            if not target.is_relative_to(directory.resolve()):
                errors.append(f"bundled reference escapes skill directory: {reference}")
            elif not target.exists():
                errors.append(f"missing bundled reference: {reference}")
    except (OSError, UnicodeError, ValueError, TypeError, yaml.YAMLError) as error:
        errors.append(str(error))
    return [f"{path}: {error}" for error in errors]


def validate(root: Path) -> tuple[int, list[str]]:
    """Return skill count and all validation failures, including early directories."""
    errors: list[str] = []
    for filename in ("plugin.json", "marketplace.json"):
        path = root / ".claude-plugin" / filename
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(metadata, dict) or not isinstance(
                metadata.get("name"), str
            ):
                raise TypeError("manifest must be an object with a name")
            if filename == "plugin.json" and not SEMVER.fullmatch(
                str(metadata.get("version", ""))
            ):
                raise ValueError("plugin version must be a semantic version")
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            errors.append(f"{path}: {error}")
    directories = sorted(path for path in (root / "skills").glob("*") if path.is_dir())
    if not directories:
        errors.append(f"{root / 'skills'}: no skills found")
    for directory in directories:
        errors.extend(validate_skill(directory))
    return len(directories), errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", type=Path, nargs="?", default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    count, errors = validate(args.root)
    for error in errors:
        print(error)
    if errors:
        print(f"Validation failed: {len(errors)} issue(s) across {count} skills")
        return 1
    print(f"Validated {count} skills: manifests, YAML metadata, and bundled references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
