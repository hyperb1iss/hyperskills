---
name: ruff
description: Use this skill when linting, formatting, or fixing Python code with ruff. Activates on mentions of ruff, ruff check, ruff format, ruff fix, ruff server, ruff analyze, Python linting, Python formatting, flake8, isort, black replacement, noqa, pycodestyle, pyflakes, lint rules, ruff config, ruff.toml, autofix, per-file-ignores, language server for Python, or Python code quality.
---

# ruff — Python Linter & Formatter

ruff (v0.15.8, March 2026) is three tools in one Rust binary: linter (`ruff check`), formatter (`ruff format`), and dependency analyzer (`ruff analyze graph`). 954 rules across 57 categories. Replaces Flake8, Black, isort, pyupgrade, and dozens more.

**The built-in language server** (`ruff server`) replaces the deprecated `ruff-lsp` package (archived Dec 2025).

## Invocation

```bash
uv run ruff ...     # Project dependency (pinned version)
uvx ruff ...        # One-off (latest)
ruff ...            # Global install
```

## Rule Selection — The Critical Decision

**Default rules are minimal:** only `["E4", "E7", "E9", "F"]` — catches syntax errors and undefined names but misses most quality rules. You almost certainly need to extend this.

### select vs extend-select

| Command | Behavior |
|---------|----------|
| `select = ["E", "F", "B"]` | **Replaces** entire default set. Only these run. |
| `extend-select = ["B"]` | **Adds** to whatever `select` provides (or defaults) |

**Config inheritance trap:** When a child config specifies `select`, the parent's `ignore` list is **discarded**. This surprises people with monorepo setups.

**Specificity wins:** More specific prefixes override less specific ones. `select = ["E"]` + `ignore = ["E501"]` enables all E rules except E501.

### Recommended Selection Strategy

**New project — start broad:**
```toml
[tool.ruff.lint]
select = [
    "E", "W",    # pycodestyle
    "F",         # Pyflakes
    "I",         # isort
    "N",         # pep8-naming
    "UP",        # pyupgrade
    "B",         # flake8-bugbear
    "SIM",       # flake8-simplify
    "TC",        # flake8-type-checking
    "RUF",       # Ruff-specific
]
ignore = ["E501"]  # Let formatter handle line length
```

**Library / open source — maximum strictness:**
```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    # Formatter conflicts (MUST disable)
    "W191", "E111", "E114", "E117",
    "D206", "D300",
    "Q000", "Q001", "Q002", "Q003", "Q004",
    "COM812", "COM819",
    # Pydocstyle conflicts
    "D203", "D213",
    # Overly strict
    "D100", "D104",
    "ANN101", "ANN102",
    "FBT", "ERA001",
    "E501",
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "D", "ANN", "ARG"]
"scripts/**" = ["T20", "INP001"]
"**/__init__.py" = ["F401", "D104"]
```

**Legacy migration — incremental:**
```toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
extend-select = [
    "I",      # Step 1: import sorting (safe, auto-fixable)
    "UP",     # Step 2: pyupgrade (mostly auto-fixable)
    # "B",    # Step 3: uncomment when ready
]
```

### The ALL Selector

`select = ["ALL"]` enables every stable rule. Ruff auto-disables conflicting pairs (D203/D211, D212/D213), but being explicit is better practice. Preview rules require `preview = true` and are **not** included even with ALL.

## Formatter Behavior

### Configuration

```toml
[tool.ruff.format]
quote-style = "double"           # "double" | "single" | "preserve"
indent-style = "space"           # "space" | "tab"
skip-magic-trailing-comma = false
docstring-code-format = true     # Format code in docstrings
preview = false                  # Enable 2026 style guide
```

### Rules That CONFLICT With the Formatter

When using `ruff format`, these 13 lint rules **must** be disabled:

```toml
ignore = [
    "W191", "E111", "E114", "E117",  # Indentation
    "D206", "D300",                   # Docstring formatting
    "Q000", "Q001", "Q002", "Q003", "Q004",  # Quotes
    "COM812", "COM819",               # Commas
]
```

`ISC001` only conflicts when `ISC002` is also disabled AND `allow-multiline = false`.

### Known Deviations from Black

Ruff targets >99.9% parity with Black but has 23 intentional divergences. The most impactful:

| Deviation | Ruff | Black |
|-----------|------|-------|
| F-string interiors | Formats `{expr}` contents (stable since 0.9.0) | Does not touch f-string interiors |
| Pragma comments (`# noqa`, `# type:`) | Excluded from line width | Counted in line width |
| Implicit string concat | Merges when fits on one line | Splits more aggressively |
| Blank lines at block start | Removes them | Preserves them (Black 24+) |
| Trailing comments | Expands statement to keep comment close | Collapses, moves comment to end |
| Single-element tuples | Always parenthesizes | Removes parens when safe |

### E501 and the Formatter

The formatter makes best-effort line wrapping — it **cannot** always succeed. Comments, long strings, and URLs may exceed `line-length`. Either ignore E501 or set `lint.pycodestyle.max-line-length` higher than `line-length`.

## Fix Safety Model

```bash
ruff check --fix .                    # Safe fixes only
ruff check --fix --unsafe-fixes .     # Include unsafe (review first!)
ruff check --fix --diff .             # Preview changes before applying
```

| Safety | Meaning | Example |
|--------|---------|---------|
| Safe | Cannot change runtime behavior | Reordering imports |
| Unsafe | May change behavior | `list(x)[0]` -> `next(iter(x))` changes exception type |

Override per-rule:
```toml
[tool.ruff.lint]
extend-safe-fixes = ["RUF015"]       # Promote to safe
extend-unsafe-fixes = ["F401"]        # Demote to unsafe (require --unsafe-fixes)
```

## Suppression System

```python
# Line-level
import os  # noqa: F401

# Block-level (new in 0.15.0)
# ruff: disable[E501]
LONG_VALUE = "..."
# ruff: enable[E501]

# File-level
# ruff: noqa: F401, E501
```

```bash
ruff check --select RUF100 --fix .    # Clean up unused noqa comments
ruff check --add-noqa .               # Auto-add noqa to all violations
```

## Preview Mode

Preview is a staging area for new rules and formatter changes.

```toml
[tool.ruff.lint]
preview = true       # Expands defaults from 59 to 412 rules
explicit-preview-rules = true  # Require individual opt-in even with preview on
```

Preview rules are NOT activated by prefix selection or `ALL` — they require preview mode enabled. Use `explicit-preview-rules = true` to control which preview rules activate individually.

## Dependency Graph Analysis

```bash
ruff analyze graph src/                          # File dependency graph (JSON)
ruff analyze graph --direction=dependents src/   # Reverse graph
ruff analyze graph --detect-string-imports src/  # Include dynamic imports
```

Use cases: selective test running, dead code detection, circular import detection.

## Configuration

**File precedence:** `.ruff.toml` > `ruff.toml` > `pyproject.toml` (nearest wins, no merging across levels).

Falls back to `~/.config/ruff/ruff.toml` when no project config exists.

```toml
[tool.ruff]
target-version = "py312"         # Inferred from requires-python if unset
line-length = 88
src = ["src", "tests"]           # First-party import classification
required-version = "==0.15.8"    # Pin version (exact match only)
extend = "../pyproject.toml"     # Inherit parent config

[tool.ruff.lint.isort]
known-first-party = ["myproject"]
combine-as-imports = true

[tool.ruff.lint.pydocstyle]
convention = "google"            # "google" | "numpy" | "pep257"

[tool.ruff.lint.flake8-type-checking]
runtime-evaluated-base-classes = ["pydantic.BaseModel"]
runtime-evaluated-decorators = ["attrs.define"]
```

For the complete rule catalog (57 categories), see `references/rules.md`.
For full configuration reference, see `references/configuration.md`.

## Debugging

```bash
ruff check --show-settings .     # Dump resolved config
ruff check --show-files .        # List files that would be checked
ruff check --statistics .        # Count violations per rule
ruff rule E501                   # Explain a specific rule
ruff linter                      # List all available linters
```

## Non-Obvious Gotchas

| Gotcha | Explanation |
|--------|-------------|
| TCH -> TC rename | `TCH` prefix is now legacy alias for `TC`. Use `TC` in new configs |
| No third-party plugins | Ruff re-implements Flake8 plugins in Rust. Cannot install additional ones |
| isort differences | Some edge cases differ from real isort (aliased imports, inline comments) |
| Notebooks: per-cell scope | E402 checked per-cell, not per-file. Each cell is its own module scope |
| `--fix` can break code | Even "safe" fixes can break dynamic Python. Review diffs for F401, UP, B rules |
| `ruff-lsp` is dead | Use `ruff server` (built into binary). The separate `ruff-lsp` package was archived Dec 2025 |
| Range formatting | `ruff format --range=10:1-20:1` formats only lines 10-20 (single file, not notebooks) |

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Blanket `# noqa` on every line | Fix the violations or use per-file-ignores |
| `select = ["ALL"]` with no `ignore` | Always pair with formatter conflict rules and overly strict rules |
| Running `ruff format` before `ruff check --fix` | Lint fixes first (may reorder imports), then format |
| Using `ruff-lsp` | Switch to `ruff server` (built-in, maintained) |
| Ignoring E501 without using formatter | Either use `ruff format` OR enforce E501, not neither |
| `select` in child config without knowing it resets | Use `extend-select` to preserve parent's rule set |

## What This Skill is NOT

- Not a replacement for `ruff --help` or `ruff rule <CODE>` for specific rule docs
- Not for type checking (use ty)
- Not for package management (use uv)
- Not for third-party Flake8 plugins that ruff hasn't re-implemented
