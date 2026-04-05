# Docker & CI/CD Patterns for uv

## Docker — Optimized Multi-Stage Build

```dockerfile
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Layer 1: Install deps only (cached unless lock changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Layer 2: Install project code
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Final stage: just the venv
FROM python:3.13-slim
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["my_app"]
```

### Docker Environment Variables

| Variable              | Value  | Purpose                                                             |
| --------------------- | ------ | ------------------------------------------------------------------- |
| `UV_COMPILE_BYTECODE` | `1`    | Faster startup in production                                        |
| `UV_LINK_MODE`        | `copy` | **Required** for cache mounts (hardlinks fail across FS boundaries) |
| `UV_NO_CACHE`         | `1`    | Reduce image size (if not using cache mounts)                       |
| `UV_PYTHON_DOWNLOADS` | `0`    | Don't download Python in container (use base image's)               |
| `UV_NO_DEV`           | `1`    | Exclude dev dependencies                                            |
| `UV_FROZEN`           | `1`    | Don't update lockfile during build                                  |

### Docker Tips

- Add `.venv` to `.dockerignore` — prevents local environments from being copied
- Use `--no-editable` in production images — avoids `.pth` file overhead
- The `--mount=type=bind` pattern avoids COPY for lock/pyproject — better cache hits
- For workspace builds, bind the entire workspace root

### Hardened Images (0.10.8+)

Astral publishes hardened Docker images with SBOM attestations:

```dockerfile
FROM ghcr.io/astral-sh/uv:0.11.2  # Full image with uv
FROM ghcr.io/astral-sh/uv:0.11.2-python3.13-bookworm  # With Python
```

## GitHub Actions

### Basic Test Matrix

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true
      - run: uv sync --locked --all-extras --all-groups
      - run: uv run pytest tests
```

### Lockfile Verification

```yaml
- run: uv lock --check # Fails if lockfile is stale
```

### Trusted Publishing (No Credentials)

```yaml
name: Publish
on:
  push:
    tags: [v*]
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
      - run: uv python install 3.13
      - run: uv build
      - run: uv publish
```

PEP 740 attestations are discovered and uploaded automatically. Use `--no-attestations` if a registry rejects them.

## Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.11.2
    hooks:
      - id: uv-lock # Keep uv.lock in sync
      - id: uv-export # Keep requirements.txt in sync
```

## PyTorch Configuration

### Automatic GPU Detection

```bash
uv pip install torch --torch-backend=auto    # Detects CUDA/ROCm/CPU
UV_TORCH_BACKEND=cu128 uv sync              # Explicit backend
```

### Project-Level Per-Platform Config

```toml
[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", marker = "sys_platform != 'linux'" },
  { index = "pytorch-cu128", marker = "sys_platform == 'linux'" },
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```

### Conflict-Based Extras (Recommended)

```toml
[project.optional-dependencies]
cpu = ["torch>=2.9.1"]
cu128 = ["torch>=2.9.1"]

[tool.uv]
conflicts = [[{extra = "cpu"}, {extra = "cu128"}]]

[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", extra = "cpu" },
  { index = "pytorch-cu128", extra = "cu128" },
]
```

Install with: `uv sync --extra cu128`
