# uv Configuration Reference

## File Locations

| Location | Format | Scope |
|----------|--------|-------|
| `pyproject.toml` `[tool.uv]` | Nested under `[tool.uv]` | Project |
| `uv.toml` | Top-level (no `[tool.uv]` prefix) | Project |
| `~/.config/uv/uv.toml` | Top-level | User |
| `/etc/uv/uv.toml` | Top-level | System |

`uv.toml` takes precedence over `pyproject.toml` in the same directory. In workspaces, only workspace root config is read.

## All Settings

### Project Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `required-version` | str | — | Enforce uv version (PEP 440 specifier) |
| `package` | bool | `true` | Treat as Python package vs virtual project |
| `managed` | bool | `true` | Whether uv manages this project |
| `default-groups` | list | `["dev"]` | Groups installed by default |
| `add-bounds` | str | `"lower"` | Default bounds for `uv add` (`lower`/`major`/`minor`/`exact`) |

### Resolution Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `resolution` | str | `"highest"` | `highest`/`lowest`/`lowest-direct` |
| `fork-strategy` | str | `"requires-python"` | `requires-python`/`fewest` |
| `prerelease` | str | `"if-necessary-or-explicit"` | Pre-release strategy |
| `exclude-newer` | str | — | Date, duration, or ISO 8601 cutoff |
| `environments` | list | `[]` | Limit lockfile to these platforms |
| `required-environments` | list | `[]` | Require wheels for these platforms |
| `conflicts` | list | `[]` | Mutually exclusive extras/groups |
| `override-dependencies` | list | `[]` | Replace declared dependency ranges |
| `constraint-dependencies` | list | `[]` | Narrow acceptable version ranges |
| `extra-build-dependencies` | map | `{}` | Additional build deps per package |

### Installation Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `compile-bytecode` | bool | `false` | Compile .pyc after install |
| `link-mode` | str | platform default | `clone`/`copy`/`hardlink`/`symlink` |
| `concurrent-downloads` | int | 50 | Max parallel downloads |
| `concurrent-builds` | int | CPU cores | Max parallel builds |
| `concurrent-installs` | int | CPU cores | Max parallel installs |
| `reinstall` | bool | `false` | Force reinstall all packages |

### Python Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `python-preference` | str | `"managed"` | `managed`/`only-managed`/`system`/`only-system` |
| `python-downloads` | str | `"automatic"` | `automatic`/`manual`/`never` |
| `torch-backend` | str | — | PyTorch backend (`cpu`/`cu126`/`cu128`/`auto`) |

### Index Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `index-strategy` | str | `"first-index"` | How to search multiple indexes |
| `keyring-provider` | str | `"disabled"` | Keyring auth provider |
| `no-build-isolation-package` | list | `[]` | Skip build isolation for these |

### Preview Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `preview` | bool | `false` | Enable all preview features |
| `preview-features` | list | `[]` | Enable specific preview features |

## Critical Environment Variables

| Variable | Purpose |
|----------|---------|
| `UV_PROJECT_ENVIRONMENT` | Override venv location (default `.venv`) |
| `UV_PYTHON` | Default Python interpreter |
| `UV_TORCH_BACKEND` | PyTorch backend selection |
| `UV_CACHE_DIR` | Cache directory |
| `UV_LINK_MODE` | Installation link mode |
| `UV_NO_DEV` | Exclude dev deps |
| `UV_FROZEN` | Don't update lockfile |
| `UV_LOCKED` | Assert lockfile unchanged |
| `UV_SYSTEM_PYTHON` | Use system Python |
| `UV_PYTHON_DOWNLOADS` | Control Python auto-download |
| `UV_PYTHON_INSTALL_MIRROR` | Custom Python download mirror |
| `UV_PREVIEW` | Enable all preview features |
| `UV_PREVIEW_FEATURES` | Enable specific preview features |
| `UV_VENV_RELOCATABLE` | Make venvs relocatable |
| `UV_INDEX_{name}_USERNAME` | Per-index auth username |
| `UV_INDEX_{name}_PASSWORD` | Per-index auth password |
| `UV_GIT_LFS` | Enable Git LFS fetching |
| `UV_WORKING_DIR` | Override working directory |
| `UV_ENV_FILE` | Dotenv files to load (space-separated) |
| `UV_NO_ENV_FILE` | Disable .env loading |
| `UV_COMPILE_BYTECODE` | Compile .pyc on install |
| `UV_NO_CACHE` | Disable caching entirely |

## Example: Complete Project Config

```toml
[tool.uv]
required-version = ">=0.11"
python-preference = "managed"
compile-bytecode = true
add-bounds = "lower"
default-groups = ["dev", "lint"]
fork-strategy = "requires-python"

[[tool.uv.index]]
name = "internal"
url = "https://pypi.internal.com/simple/"
default = true

[tool.uv.sources]
my-lib = { workspace = true }
torch = { index = "pytorch-cpu" }
```

## Example: uv.toml (Standalone)

```toml
# No [tool.uv] prefix — top-level keys
required-version = ">=0.11"
python-preference = "managed"
compile-bytecode = true

[[index]]
name = "internal"
url = "https://pypi.internal.com/simple/"

[pip]
index-url = "https://pypi.org/simple"
```
