---
name: ty
description: Use this skill when type checking Python code or setting up type checking with ty. Activates on mentions of ty, ty check, ty server, Python type checking, type checker, mypy replacement, pyright replacement, type annotations, type errors, type ignore, Python types, LSP, language server, or Python static analysis.
---

# ty — Python Type Checker & Language Server

ty (v0.0.32, Apr 2026) is Astral's Rust-based Python type checker and language server. **Beta status** — 0.0.x versioning, breaking changes between versions, and no stable API yet. Astral reports 10-100x faster checks than mypy and Pyright on large projects.

**Formerly "Red-Knot"** — renamed May 2025, extracted from the ruff repo to `astral-sh/ty`.

## When to Use ty

- `[tool.ty]` section in `pyproject.toml` or `ty.toml` exists
- Type checking Python code in any project
- Setting up an LSP for Python in your editor

**When to wait:** Projects heavily dependent on mypy plugins (Pydantic, Django, SQLAlchemy). ty has no plugin system and no plans to add one — first-class framework support is the stated approach instead.

## How to Invoke

```bash
uvx ty check                  # One-off (latest)
uv run ty check               # Project dependency
ty check                      # Global install
```

## CLI Commands

```bash
# Type checking
ty check                           # Check current directory
ty check path/to/file.py           # Specific file
ty check src/ tests/               # Multiple directories

# Rule severity
ty check --error unresolved-import
ty check --warn division-by-zero
ty check --ignore unresolved-attribute

# Python targeting
ty check --python-version 3.12
ty check --python-platform linux
ty check --python .venv/bin/python

# Output formats
ty check --output-format full      # Rich diagnostics (default)
ty check --output-format concise   # One line per error
ty check --output-format github    # GitHub Actions annotations
ty check --output-format gitlab    # GitLab Code Quality
ty check --output-format junit     # JUnit XML

# Watch mode
ty check --watch                   # Re-check on file changes
ty check -W                        # Short form

# Migration helper
ty check --add-ignore              # Auto-add ty: ignore comments for all errors

# Introspection
ty explain rule                    # List all rules
ty explain rule invalid-assignment # Explain specific rule

# Language server
ty server                          # Start LSP
```

### Exit Codes

| Code | Meaning                                                      |
| ---- | ------------------------------------------------------------ |
| `0`  | No errors (warnings don't count unless `--error-on-warning`) |
| `1`  | Type errors found                                            |
| `2`  | CLI/configuration error                                      |

## Configuration

ty reads from `ty.toml` (takes precedence) or `pyproject.toml` under `[tool.ty]`.

```toml
[tool.ty.environment]
python-version = "3.12"          # 3.7-3.15 allowed; unset falls back to 3.14
python-platform = "linux"        # win32|darwin|android|ios|linux|all
python = ".venv"                 # Path to environment/interpreter
root = ["src"]                   # First-party module discovery
extra-paths = []                 # Additional resolution paths

[tool.ty.rules]
unresolved-import = "error"
division-by-zero = "ignore"
possibly-unresolved-reference = "warn"

[tool.ty.analysis]
allowed-unresolved-imports = ["mypackage._internal.*"]
replace-imports-with-any = ["legacy_lib.*"]
respect-type-ignore-comments = true

[tool.ty.src]
include = ["src/**/*.py"]
exclude = ["**/migrations/**"]
respect-ignore-files = true

[tool.ty.terminal]
output-format = "full"
error-on-warning = false
```

### Per-File Overrides

```toml
[[tool.ty.overrides]]
include = ["tests/**", "**/test_*.py"]

[tool.ty.overrides.rules]
possibly-unresolved-reference = "warn"
unresolved-attribute = "ignore"
```

## Suppression Comments

```python
# Preferred: rule-specific
x = foo  # ty: ignore[possibly-unresolved-reference]

# Broad (discouraged)
x = foo  # ty: ignore

# Legacy (honored by default, configurable)
x = foo  # type: ignore
```

**Rule:** Fix type errors instead of suppressing. Only add ignore comments when explicitly requested. Always prefer rule-specific ignores.

## What Makes ty Unique

### Unknown vs Any

ty distinguishes between `Any` (deliberate opt-out) and `Unknown` (inferred gap). This is the "gradual guarantee" — all code is checked, but unknowns are treated permissively rather than skipped entirely (mypy skips unannotated functions by default).

### Intersection Types

ty supports `A & B` intersection types natively — not available in mypy or pyright.

### Fine-Grained Incrementality

Built on Salsa (same framework as rust-analyzer). Changing one function re-parses only that function and its dependents, not the entire file. This powers sub-millisecond editor responses.

### Performance

| Project               | ty        | pyright | mypy   |
| --------------------- | --------- | ------- | ------ |
| home-assistant (cold) | 2.19s     | 19.62s  | 45.66s |
| PyTorch (cold)        | 4.04s     | 262.74s | —      |
| PyTorch (incremental) | **4.7ms** | 386ms   | —      |

## Editor/LSP Setup

ty ships a full LSP with go-to-definition, find references, auto-complete with auto-import, rename, inlay hints, and hover.

**VS Code:** Install `astral-sh.ty` extension.

**Neovim (>=0.11):**

```lua
vim.lsp.config('ty', { settings = { ty = {} } })
vim.lsp.enable('ty')
```

**Neovim (<0.11):**

```lua
require('lspconfig').ty.setup({ settings = { ty = {} } })
```

**Zed:** Built-in, enable in settings:

```json
{ "languages": { "Python": { "language_servers": ["ty", "ruff"] } } }
```

**PyCharm:** Native support in 2025.3+.

**Any LSP client:** Run `ty server` and connect.

## Integration with Ruff

ty and ruff are complementary:

| Tool     | Role                                               |
| -------- | -------------------------------------------------- |
| **ruff** | Linting (style, correctness, imports) + formatting |
| **ty**   | Type checking + language server                    |

ty has **no strict mode** for requiring annotations. Use ruff's `ANN001`/`ANN201` rules instead. Both LSPs can run simultaneously in editors.

## Current Limitations (Beta)

| Limitation                         | Impact                                    | Workaround                             |
| ---------------------------------- | ----------------------------------------- | -------------------------------------- |
| **No plugin system**               | No Pydantic/Django/SQLAlchemy plugins     | Wait for first-class framework support |
| **No strict mode**                 | Can't require annotations                 | Use ruff ANN rules                     |
| **No pre-commit hook**             | Must set up manually                      | `uvx ty check` in custom hook          |
| **No TypeVarTuple/Unpack**         | NumPy/tensor typing limited               | Use mypy for these                     |
| **No TypedDict functional syntax** | `TD = TypedDict("TD", ...)` not supported | Use class syntax                       |
| **Beta stability**                 | Breaking changes between versions         | Pin version, test upgrades             |
| **Script deps ignored**            | PEP 723 inline metadata not recognized    | Run ty in project context              |
| **Limited monorepo support**       | No automatic multi-root discovery         | Configure root paths manually          |

For the full type system feature matrix, see `references/type-system.md`.
For detailed migration tables from mypy/pyright, see `references/migration.md`.

## Migration Strategy

### Quick Start (Parallel Adoption)

1. Run `ty check --add-ignore` to auto-suppress all current errors as baseline
2. Add ty to CI as **non-blocking** alongside existing type checker
3. Gradually remove `ty: ignore` comments
4. Switch ty to blocking once comfortable

### From mypy

```bash
mypy .                        ->  ty check
mypy --strict .               ->  ty check --error-on-warning  # (partial)
mypy -p mypackage             ->  ty check src/mypackage/      # paths, not modules
mypy --python-version 3.11    ->  ty check --python-version 3.11
```

### From pyright

```bash
pyright .                     ->  ty check
pyright path/to/file.py       ->  ty check path/to/file.py
```

## Anti-Patterns

| Anti-Pattern                                        | Fix                                                          |
| --------------------------------------------------- | ------------------------------------------------------------ |
| Blanket `# ty: ignore` everywhere                   | Fix errors or use rule-specific ignores                      |
| Using `# type: ignore` in new code                  | Use `# ty: ignore[rule-name]`                                |
| Expecting mypy plugin behavior                      | Check limitation table; wait for framework support if needed |
| Running ty on unannotated code expecting strictness | Add ruff ANN rules for annotation enforcement                |
| Pinning to latest without testing                   | Pin version in CI, test upgrades deliberately                |

## What This Skill is NOT

- Not a replacement for `ty explain rule <name>` for rule details
- Not for linting or formatting (use ruff)
- Not for package management (use uv)
- Not a mypy drop-in replacement yet (plugin gap, beta stability)
