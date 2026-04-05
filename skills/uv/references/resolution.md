# Dependency Resolution Deep Dive

## Resolution Strategies

| Strategy            | Flag                         | Behavior                                   |
| ------------------- | ---------------------------- | ------------------------------------------ |
| `highest` (default) | —                            | Latest compatible versions                 |
| `lowest`            | `--resolution lowest`        | Minimum versions for all deps              |
| `lowest-direct`     | `--resolution lowest-direct` | Minimum for direct, highest for transitive |

## Universal vs Platform-Specific

**Universal** (`uv.lock`, default): Portable across all platforms and Python versions. Lists packages multiple times with different versions per platform via fork markers.

**Platform-specific** (`uv pip compile`): Resolves for current platform only. Cross-compile with `--python-platform` and `--python-version`.

## Fork Strategy

```toml
[tool.uv]
fork-strategy = "requires-python"  # Default: latest per Python version
# fork-strategy = "fewest"         # Minimize version count across platforms
```

## Environment Constraints

```toml
[tool.uv]
# Narrow resolution to these platforms only
environments = ["sys_platform == 'darwin'", "sys_platform == 'linux'"]

# REQUIRE wheels to exist for these (fail if missing)
required-environments = ["sys_platform == 'linux' and platform_machine == 'aarch64'"]
```

## Overrides vs Constraints

| Feature                  | Overrides             | Constraints                |
| ------------------------ | --------------------- | -------------------------- |
| Purpose                  | Replace declared deps | Narrow acceptable versions |
| Adds packages?           | No                    | No                         |
| Can expand versions?     | **Yes**               | No                         |
| Affects undeclared deps? | No                    | No                         |

```toml
[tool.uv]
override-dependencies = ["numpy>=1.24,<2"]      # Force version range
constraint-dependencies = ["requests>=2.28"]     # Floor only
```

**Use overrides** when a transitive dependency declares an incorrect upper bound. **Use constraints** to enforce minimum versions globally.

## Dependency Metadata (Skip Source Builds)

```toml
[[tool.uv.dependency-metadata]]
name = "chumpy"
version = "0.70"
requires-dist = ["numpy>=1.8.1", "scipy>=0.13.0"]
```

Provides static metadata without building source distributions — useful for packages with exotic build requirements (CUDA, Fortran, etc.).

## Conflict Declaration

```toml
[tool.uv]
conflicts = [
  [
    { extra = "cpu" },
    { extra = "gpu" },
  ]
]
```

Tells the resolver these extras are mutually exclusive — prevents impossible resolution.

## Reproducibility

```toml
[tool.uv]
exclude-newer = "2026-03-01T00:00:00Z"   # RFC 3339 timestamp
exclude-newer = "30 days"                  # Relative duration
exclude-newer = "PT24H"                    # ISO 8601 duration
```

Per-package: `exclude-newer-package` setting.

## Pre-release Handling

Pre-releases accepted only when:

1. Directly specified with pre-release qualifier (e.g., `flask>=2.0.0rc1`)
2. All published versions are pre-releases
3. `--prerelease allow` flag used

## Sources

```toml
[tool.uv.sources]
# Workspace member
my-lib = { workspace = true }

# Git (tag, branch, or rev)
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
langchain = { git = "https://github.com/langchain-ai/langchain", subdirectory = "libs/langchain" }

# Local path (editable or not)
my-lib = { path = "../libs/my-lib", editable = true }

# URL
httpx = { url = "https://example.com/httpx-0.27.0.tar.gz" }

# Index (explicit registry)
torch = { index = "pytorch" }

# Platform-specific sources
httpx = [
  { git = "https://github.com/encode/httpx", tag = "0.27.2", marker = "sys_platform == 'darwin'" },
  { git = "https://github.com/encode/httpx", tag = "0.24.1", marker = "sys_platform == 'linux'" },
]
```

**`tool.uv.sources` are development-only.** They are stripped when building (`uv build --no-sources`) and publishing. Published packages only see `project.dependencies`.

## Index Configuration

```toml
[[tool.uv.index]]
name = "internal"
url = "https://pypi.internal.com/simple/"
default = true          # Use as default instead of PyPI

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true         # Only used when explicitly referenced in sources
```

| Setting           | Behavior                                                |
| ----------------- | ------------------------------------------------------- |
| `default = true`  | Replaces PyPI as the default index                      |
| `explicit = true` | Only packages explicitly sourced from this index use it |
| Neither           | Searched after default index                            |

**`index-strategy`** controls multi-index search:

- `first-index` (default): Use first index that has the package
- `unsafe-first-match`: Search all indexes, use first match
- `unsafe-best-match`: Search all indexes, use best version

## Lockfile Schema

- TOML format, schema-versioned by minor uv releases
- `revision` field tracks backwards-compatible changes
- uv rejects lockfiles with newer schema versions — pin `required-version` to avoid surprises
