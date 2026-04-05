---
name: uv-build
description: Use this skill when building Python packages, configuring build backends, publishing to PyPI, or setting up pyproject.toml build systems. Activates on mentions of uv build, uv_build, build backend, Python packaging, sdist, wheel, pyproject.toml build-system, PEP 517, PEP 621, uv publish, package publishing, setuptools migration, hatchling, flit, build system, or Python distribution.
---

# uv-build — Python Build Backend

`uv_build` is Astral's Rust-based build backend for Python packages. Stable since July 2025, default for `uv init`. 10-35x faster than setuptools/hatchling/flit. **Pure Python packages only** — no C/Rust extensions.

## When to Use uv-build

```
Is your package pure Python?
├─ YES → Needs VCS versioning, build hooks, or dynamic metadata?
│  ├─ NO  → uv_build (fast, zero-config, excellent defaults)
│  └─ YES → hatchling (extensible, plugin ecosystem)
└─ NO  → What kind of extensions?
   ├─ Rust (PyO3)     → maturin
   ├─ C/C++ (CMake)   → scikit-build-core
   └─ C/C++ (classic) → setuptools
```

**Migration blocker:** `dynamic = [...]` is **not supported**. Projects using `dynamic = ["version"]` with hatchling/setuptools must switch to static versions in pyproject.toml (use `uv version --bump` for version management).

## Setup

```toml
[build-system]
requires = ["uv_build>=0.11.2,<0.12"]
build-backend = "uv_build"
```

**Always include an upper bound** (`<0.12`). The build backend schema is versioned by minor version. Bump when upgrading uv.

## The Direct Build Fast Path

When uv detects `uv_build` as the backend, it **bypasses PEP 517 entirely** — calling directly into Rust code in-process. No Python subprocess, no build environment creation, no dependency installation.

This means you can **build and publish packages without Python installed** — the entire build runs in Rust.

Conditions for fast path:

- `build-backend` is exactly `"uv_build"`
- `requires` contains only `uv_build` (no extra build deps)
- Version specifier is within known compatible range

Force PEP 517 mode: `uv build --force-pep517`

## Module Discovery

**Default:** expects `src/<package_name>/__init__.py` (src layout).

```toml
[tool.uv.build-backend]
module-root = "src"          # Default (src layout)
module-root = ""             # Flat layout (package at project root)
module-name = "my_package"   # Override auto-detected name
```

### Multiple Modules

```toml
[tool.uv.build-backend]
module-name = ["foo", "bar"]
```

### Namespace Packages (PEP 420)

```toml
[tool.uv.build-backend]
module-name = "cloud.database"    # Dotted name — parent must NOT have __init__.py
```

For multiple namespace roots:

```toml
[tool.uv.build-backend]
namespace = true
module-name = ["cloud.database", "cloud.auth"]
```

### Type Stub Packages

Auto-detected from `-stubs` suffix in package name. Uses `__init__.pyi` instead of `__init__.py`.

## File Inclusion/Exclusion

```toml
[tool.uv.build-backend]
source-include = ["tests/**", "CHANGELOG.md"]    # Extra files for sdist
source-exclude = ["*.bin", "benchmarks/**"]       # Exclude from sdist AND wheel
wheel-exclude = ["tests/**"]                      # Exclude from wheel only
default-excludes = true                           # __pycache__, *.pyc (default on)
```

**Patterns:** PEP 639 portable glob syntax. Exclusions always override inclusions.

**Safety features:**

- Warns on 10k+ files (likely traversing `.venv` or `node_modules`)
- Detects virtual environments and skips them
- `pyproject.toml` + module source always included regardless of patterns

### Preview Included Files

```bash
uv build --list       # Show what would be included (no actual build)
```

## Wheel Data Directories

```toml
[tool.uv.build-backend.data]
scripts = "bin"              # -> <venv>/bin (executables)
headers = "include/mylib"    # -> include dir (C headers)
data = "share"               # -> venv root (careful: can overwrite!)
```

## Build Commands

```bash
uv build                          # Build sdist + wheel to dist/
uv build --sdist                  # Source distribution only
uv build --wheel                  # Wheel only
uv build --list                   # Preview included files
uv build --no-sources             # Test PyPI compatibility (strips tool.uv.sources)
uv build --package <name>         # Specific workspace member
uv build --build-constraints c.txt # Pin build dependency versions
uv build --require-hashes         # Hash verification for build deps
uv build --force-pep517           # Bypass fast path
```

## Publishing Workflow

```bash
uv version                        # Check current
uv version --bump minor           # 1.0.0 -> 1.1.0
uv version --bump patch --dry-run # Preview
uv build                          # Build
uv publish                        # Upload to PyPI
uv publish --check-url https://pypi.org/simple/  # Skip if already published
```

### Prevent Accidental Publication

```toml
[project]
classifiers = ["Private :: Do Not Upload"]
```

## Editable Installs

uv_build uses **static `.pth` files** for editable installs (not dynamic import hooks like setuptools). This works correctly with type checkers and IDEs out of the box — no `editable_mode = "compat"` workaround needed.

```bash
uv sync                  # Installs project as editable by default
uv pip install -e .      # Explicit editable install
```

## Metadata Validation

uv_build is **strict** about metadata:

- Rejects `project.description` with newlines
- Enforces SPDX license expressions
- Validates classifiers
- Rejects non-UTF-8 READMEs
- Blocks reserved entrypoint groups (must use `project.scripts`/`project.gui-scripts`)

**No dynamic metadata:** `dynamic = [...]` is not supported. All metadata must be static in pyproject.toml.

## Complete Example

```toml
[project]
name = "cloud-database"
version = "2.1.0"
description = "Cloud database toolkit"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
dependencies = ["sqlalchemy>=2.0"]

[project.scripts]
cloud-db = "cloud_database.cli:main"

[build-system]
requires = ["uv_build>=0.11.2,<0.12"]
build-backend = "uv_build"

[tool.uv.build-backend]
source-include = ["tests/**", "CHANGELOG.md"]
wheel-exclude = ["tests/**"]
```

## Migration from Other Backends

### From setuptools

**Prerequisites:** Pure Python, all metadata in `[project]` table (PEP 621), no `setup.py` build logic.

```toml
# BEFORE
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

# AFTER
[build-system]
requires = ["uv_build>=0.11.2,<0.12"]
build-backend = "uv_build"
```

MANIFEST.in equivalents:
| MANIFEST.in | uv_build |
|------------|----------|
| `include CHANGELOG.md` | `source-include = ["CHANGELOG.md"]` |
| `recursive-include tests` | `source-include = ["tests/**"]` |
| `global-exclude *.pyc` | Handled by `default-excludes` |
| `prune docs` | `source-exclude = ["docs/**"]` |

### From hatchling

```toml
# BEFORE
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# AFTER
[build-system]
requires = ["uv_build>=0.11.2,<0.12"]
build-backend = "uv_build"
```

**Blockers:** VCS versioning (`[tool.hatch.version]`), build hooks (`[tool.hatch.build.hooks.*]`).

### From flit

```toml
# BEFORE
[build-system]
requires = ["flit_core>=3.4"]
build-backend = "flit_core.buildapi"

# AFTER  (flit uses flat layout by default)
[build-system]
requires = ["uv_build>=0.11.2,<0.12"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = ""
```

### Verification

```bash
uv build --list          # Check included files match expectations
uv build                 # Build and inspect artifacts
uv build --no-sources    # Verify PyPI compatibility
```

## Limitations

| Limitation            | Impact                                 | Alternative                                   |
| --------------------- | -------------------------------------- | --------------------------------------------- |
| Pure Python only      | No C/C++/Cython/Rust extensions        | setuptools, maturin, scikit-build-core        |
| No dynamic metadata   | Can't derive version from VCS/git tags | hatchling + hatch-vcs, or `uv version --bump` |
| No build hooks        | No code gen, protobuf, asset bundling  | hatchling with build hooks                    |
| No setup.py/setup.cfg | Must fully convert to pyproject.toml   | Convert first, then migrate                   |
| Upper-bound pinning   | Must update `requires` when upgrading  | Manageable with `uv version` workflow         |

## Anti-Patterns

| Anti-Pattern                                  | Fix                                                     |
| --------------------------------------------- | ------------------------------------------------------- |
| Using uv_build for packages with C extensions | Use setuptools, maturin, or scikit-build-core           |
| Omitting upper bound on requires              | Always `<0.X` to prevent breaking changes               |
| `source-include = ["**/*"]`                   | Let defaults handle it; add specific patterns only      |
| Forgetting `--no-sources` test before publish | Sources are dev-only; verify PyPI-only resolution works |
| Dynamic version from `__init__.py`            | Static version in pyproject.toml + `uv version --bump`  |

## What This Skill is NOT

- Not for building C/Rust/Cython extensions
- Not for projects requiring VCS-derived versioning
- Not for complex build pipelines needing hooks
- Not a uv project management guide (see uv skill)
