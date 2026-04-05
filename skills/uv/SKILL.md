---
name: uv
description: Use this skill when working with Python projects, packages, scripts, environments, or dependencies using uv. Activates on mentions of uv, uv add, uv sync, uv run, uv lock, uv init, uv build, uv publish, uv export, uv python, uvx, uv tool, uv pip, uv venv, uv workspace, uv audit, uv version, pyproject.toml dependencies, Python package management, Python project setup, dependency lockfile, or virtual environments.
---

# uv — Python Package & Project Manager

uv (v0.11, March 2026) replaces pip, pip-tools, pipx, pyenv, virtualenv, and poetry. Written in Rust, 10-100x faster than alternatives. Now downloads Python from Astral's own mirror by default.

## Workflow Decision Tree

```
What are you doing?
├─ Running a standalone script? ──────────────────── Scripts workflow
│  (single .py file, no project context needed)
├─ Working in a project with pyproject.toml? ─────── Projects workflow
│  (adding deps, running commands, building)
├─ Running a CLI tool (ruff, ty, pytest)? ────────── Tools workflow
│  (one-off execution, not project-scoped)
├─ Managing Python versions? ─────────────────────── Python workflow
│  (installing, pinning, upgrading interpreters)
├─ Legacy requirements.txt workflow? ─────────────── Pip interface
│  (no pyproject.toml, existing req files)
└─ Building/publishing a package? ────────────────── Build/Publish workflow
   (sdist, wheel, PyPI upload)
```

**Critical rule:** If `pyproject.toml` exists, use project commands (`uv add`, `uv sync`, `uv run`). Never `uv pip install` in a project — it bypasses the lockfile.

## Projects

### Initialization

```bash
uv init                              # App (main.py, no build system)
uv init --lib                        # Library (src/ layout, uv_build backend, py.typed)
uv init --package                    # Packaged app (src/ layout, entry points)
uv init --build-backend uv_build     # Explicit backend choice
uv init --build-backend maturin      # Rust extension module
uv init --python 3.13                # Specific Python version
uv init --bare                       # pyproject.toml only
```

### Dependency Management

```bash
uv add httpx                         # Add to project.dependencies
uv add httpx --dev                   # Add to dependency-groups.dev
uv add httpx --group lint            # Add to dependency-groups.lint
uv add httpx --optional network      # Add to project.optional-dependencies.network
uv add -r requirements.txt           # Import from requirements file
uv remove httpx                      # Remove dependency

# Version bounds (configurable default via add-bounds setting)
uv add 'httpx>=0.27'                 # Lower bound (default behavior)
uv add 'httpx~=0.27.0'              # Compatible release
```

### Dependency Groups (PEP 735)

```toml
[dependency-groups]
dev = ["pytest>=8", "ruff"]
lint = ["ruff"]
test = ["pytest", {include-group = "lint"}]  # Nest groups

[tool.uv]
default-groups = ["dev", "lint"]  # Synced by default
```

### Sync & Run

```bash
uv sync                              # Install from lockfile
uv sync --locked                     # Error if lockfile stale (use in CI)
uv sync --frozen                     # Use lockfile as-is, no update
uv sync --no-dev                     # Skip dev dependencies
uv sync --all-extras                 # All optional dependencies
uv sync --all-groups                 # All dependency groups
uv sync --group lint                 # Include specific group
uv sync --no-install-project         # Deps only (Docker layer caching)
uv sync --inexact                    # Don't remove extraneous packages

uv run pytest                        # Run in project environment
uv run --with hypothesis pytest      # Ad-hoc extra dependency
uv run -p 3.12 pytest                # Specific Python version
```

### Locking

```bash
uv lock                              # Resolve and lock dependencies
uv lock --upgrade                    # Upgrade all to latest compatible
uv lock --upgrade-package httpx      # Upgrade specific package
uv lock --check                      # Verify lockfile current (CI)
uv lock --resolution lowest          # Minimum compatible versions
```

### Export

```bash
uv export --format requirements-txt  # requirements.txt
uv export --format pylock-toml       # PEP 751 (preview)
```

## Scripts (PEP 723)

Single-file scripts with inline dependency metadata. **Scripts with metadata run in complete isolation** — project dependencies are ignored even inside a project directory.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "rich>=13"]
# [tool.uv]
# exclude-newer = "2026-03-01T00:00:00Z"
# ///

import httpx
```

```bash
uv run script.py                     # Run with inline deps
uv add --script script.py 'click'    # Add dep to script metadata
uv lock --script script.py           # Create script.py.lock
uv init --script example.py          # Create script with metadata template
echo 'print("hi")' | uv run -       # Read from stdin
```

## Tools

```bash
uvx ruff check .                     # Run tool in isolated env
uvx ruff@0.15.8 check .             # Specific version
uvx --from 'httpie' http             # Package name differs from command
uvx --python 3.12 ruff              # With specific Python

uv tool install ruff                 # Persistent install to PATH
uv tool upgrade --all                # Upgrade all installed tools
uv tool list --outdated              # Show available updates (0.10.10+)
```

**Key distinction:** `uvx` creates isolated environments — tools are CLI-only, not importable. For tools needing project context (pytest, mypy), use `uv run` inside a project.

## Python Management

```bash
uv python install 3.13               # Install latest patch
uv python install 3.13t              # Free-threaded (no GIL)
uv python install pypy               # PyPy implementation
uv python upgrade 3.13               # Upgrade to latest patch (0.10.0+)
uv python pin 3.13                   # Create .python-version
uv python list --only-installed      # Show installed versions
```

| Preference Setting  | Behavior                   |
| ------------------- | -------------------------- |
| `managed` (default) | Prefer uv-installed Python |
| `only-managed`      | Never use system Python    |
| `system`            | Prefer system Python       |
| `only-system`       | Never use managed Python   |

## Workspaces

```toml
# Root pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental"]

[tool.uv.sources]
my-lib = { workspace = true }
```

Key behaviors:

- **Single lockfile** across all members
- **Single `requires-python`** — intersection of all members
- Workspace members are always **editable**
- Root `tool.uv.sources` apply to all members unless overridden
- Config in `uv.toml` is read only from workspace root — member-level config is **ignored**

```bash
uv workspace dir                     # Print workspace root
uv workspace list                    # List members
uv run --package my-lib pytest       # Run in specific member context
uv build --package my-lib            # Build specific member
```

**Virtual workspaces** (no root package):

```toml
[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/*"]
```

## Publishing

```bash
uv version                           # Read current version
uv version --bump minor              # 1.0.0 -> 1.1.0
uv version --bump patch --dry-run    # Preview change
uv build                             # Build sdist + wheel
uv build --list                      # Preview included files
uv publish                           # Publish to PyPI
uv publish --token pypi-xxx          # With API token
uv publish --index testpypi          # Custom registry
uv publish --check-url https://pypi.org/simple/  # Skip if exists
```

Trusted publishing (GitHub Actions, no credentials):

```yaml
permissions:
  id-token: write
steps:
  - run: uv build && uv publish
```

## Preview Features (0.10+)

Enable with `--preview` or `UV_PREVIEW=1`, or selectively with `--preview-features`:

| Feature       | Flag          | Description                                    |
| ------------- | ------------- | ---------------------------------------------- |
| `uv audit`    | `--preview`   | Security vulnerability scanning (OSV database) |
| `uv format`   | `format`      | Code formatting via Ruff                       |
| `pylock`      | `pylock`      | Install from `pylock.toml` (PEP 751)           |
| `native-auth` | `native-auth` | System keychain credentials                    |

```bash
uv audit --preview                   # Scan for vulnerabilities
```

## Configuration Quick Reference

**Precedence:** CLI flags > env vars > project `uv.toml` > project `pyproject.toml [tool.uv]` > user `~/.config/uv/uv.toml` > system `/etc/uv/uv.toml`

In a workspace, config search starts at workspace root. `uv.toml` takes precedence over `pyproject.toml` in the same directory.

| Setting            | Default             | Purpose                                  |
| ------------------ | ------------------- | ---------------------------------------- |
| `required-version` | —                   | Enforce uv version (PEP 440)             |
| `add-bounds`       | `"lower"`           | Default bounds for `uv add`              |
| `compile-bytecode` | `false`             | Compile .pyc on install                  |
| `fork-strategy`    | `"requires-python"` | Resolution fork behavior                 |
| `exclude-newer`    | —                   | Date/duration cutoff for reproducibility |
| `environments`     | `[]`                | Limit lockfile platforms                 |
| `torch-backend`    | —                   | PyTorch backend (cpu/cu126/auto)         |
| `default-groups`   | `["dev"]`           | Groups installed by default              |

**.env file support:** `uv run` automatically loads `.env` files. Control with `--env-file` or `UV_NO_ENV_FILE=1`.

For full configuration reference, see `references/configuration.md`.
For Docker and CI/CD patterns, see `references/docker-ci.md`.
For dependency resolution deep dive, see `references/resolution.md`.

## Non-Obvious Gotchas

| Gotcha                                | Explanation                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------- |
| `uv pip install` in a project         | Bypasses lockfile and pyproject.toml. Use `uv add` instead                      |
| Scripts with metadata ignore project  | Even inside a project dir, PEP 723 scripts run in isolation                     |
| `--locked` vs `--frozen`              | `--locked` errors on stale lockfile; `--frozen` silently uses whatever's there  |
| `uv venv` needs `--clear` (0.10+)     | No longer auto-removes existing venvs                                           |
| `tool.uv.sources` stripped on publish | Sources are development-only; published packages use `project.dependencies`     |
| Workspace config inheritance          | Member-level `uv.toml` is ignored; only workspace root config applies           |
| `link-mode` in Docker                 | Must use `copy` with cache mounts (hardlinks fail across filesystem boundaries) |
| `exclude-newer` accepts durations     | `"30 days"`, `"1 week"`, `"PT24H"` — not just RFC 3339 timestamps               |
| `uv run` uses inexact sync            | Won't remove extraneous packages by default; use `--exact` to enforce           |

## Anti-Patterns

| Anti-Pattern                                        | Fix                                                      |
| --------------------------------------------------- | -------------------------------------------------------- |
| `pip install` / `python -m pip` in uv project       | `uv add <package>` for deps, `uv run` for commands       |
| `python script.py`                                  | `uv run script.py` (ensures correct environment)         |
| `python -m venv .venv && source .venv/bin/activate` | `uv run <command>` (auto-manages venv)                   |
| Manual `requirements.txt` for new projects          | `uv init` + `uv add` + `uv.lock`                         |
| `uv pip compile` for project deps                   | `uv lock` (universal resolution)                         |
| `uv tool install pytest`                            | `uv add --dev pytest` + `uv run pytest` (project-scoped) |
| `uvx` for project-scoped tools                      | `uv run <tool>` (picks up project context)               |

## What This Skill is NOT

- Not a replacement for reading `uv --help` for flag discovery
- Not for Poetry/PDM projects (those have their own lock formats)
- Not for building C/Rust extensions (see uv-build skill for backend limitations)
- Not for ruff/ty configuration (see dedicated ruff and ty skills)
