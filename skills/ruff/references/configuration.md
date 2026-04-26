# Ruff Configuration Reference

## File Precedence

`.ruff.toml` > `ruff.toml` > `pyproject.toml` (nearest wins, no merging across directory levels)

User-level fallback: `~/.config/ruff/ruff.toml` (Linux/macOS) or `~\AppData\Roaming\ruff\ruff.toml` (Windows)

## pyproject.toml vs ruff.toml

```toml
# pyproject.toml              # ruff.toml (no [tool.ruff] prefix)
[tool.ruff]                   line-length = 100
line-length = 100
                              [lint]
[tool.ruff.lint]              select = ["E", "F"]
select = ["E", "F"]
                              [format]
[tool.ruff.format]            quote-style = "single"
quote-style = "single"
                              [lint.isort]
[tool.ruff.lint.isort]        known-first-party = ["mymod"]
known-first-party = ["mymod"]
```

## Config Inheritance

```toml
[tool.ruff]
extend = "../pyproject.toml"  # Inherit parent config, override locally
```

## Top-Level Settings

```toml
[tool.ruff]
target-version = "py312"      # py37-py315, inferred from requires-python if unset
line-length = 88
indent-width = 4
src = ["src", "tests"]        # First-party import classification
required-version = "==0.15.12" # Pin version with a PEP 440 specifier
respect-gitignore = true
include = ["*.py", "*.pyi"]
exclude = [".venv", "migrations"]
extend-include = ["*.ipynb"]
extend-exclude = ["generated"]
per-file-target-version = { "legacy/**" = "py38" }
```

## Lint Settings

```toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]  # Baseline (replaces defaults)
extend-select = ["B", "I"]         # Additive
ignore = ["E501"]                   # Subtractive
fixable = ["ALL"]                   # Which rules can be auto-fixed
unfixable = ["F401"]                # Block auto-fix for these
extend-safe-fixes = ["RUF015"]     # Promote to safe
extend-unsafe-fixes = ["F401"]     # Demote to unsafe
preview = false
explicit-preview-rules = false     # Require individual preview opt-in
task-tags = ["TODO", "FIXME", "XXX", "HACK"]
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"
external = ["V"]                   # Preserve in noqa for external tools
logger-objects = ["myapp.logging.logger"]
typing-modules = ["myapp.types"]
```

## Per-File Ignores

```toml
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "E402"]
"**/{tests,docs}/*" = ["S101", "D"]
"**/conftest.py" = ["ARG"]
"scripts/**" = ["T20", "INP001"]
"*.ipynb" = ["T20", "E402"]
"migrations/**" = ["E501"]
```

## Lint Sub-Settings

### isort

```toml
[tool.ruff.lint.isort]
known-first-party = ["myproject"]
known-third-party = ["wandb"]
combine-as-imports = true
force-single-line = false           # WARNING: conflicts with formatter
lines-after-imports = 2
required-imports = ["from __future__ import annotations"]
```

### pydocstyle

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"               # "google" | "numpy" | "pep257"
```

### pylint

```toml
[tool.ruff.lint.pylint]
max-args = 5
max-returns = 6
max-branches = 12
max-statements = 50
max-locals = 15
max-nested-blocks = 5
max-bool-expr = 5
max-public-methods = 20
allow-magic-value-types = ["int", "str"]
```

### mccabe

```toml
[tool.ruff.lint.mccabe]
max-complexity = 10
```

### flake8-type-checking

```toml
[tool.ruff.lint.flake8-type-checking]
runtime-evaluated-base-classes = ["pydantic.BaseModel"]
runtime-evaluated-decorators = ["attrs.define"]
quote-annotations = false
strict = false
```

### flake8-tidy-imports

```toml
[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "parents"
banned-api = { "os.path.join" = { msg = "Use pathlib.Path instead" } }
```

### flake8-import-conventions

```toml
[tool.ruff.lint.flake8-import-conventions.aliases]
numpy = "np"
pandas = "pd"
matplotlib.pyplot = "plt"
seaborn = "sns"
polars = "pl"
```

### flake8-pytest-style

```toml
[tool.ruff.lint.flake8-pytest-style]
fixture-parentheses = false
mark-parentheses = false
```

### flake8-builtins

```toml
[tool.ruff.lint.flake8-builtins]
ignorelist = ["id", "type"]
```

### pycodestyle

```toml
[tool.ruff.lint.pycodestyle]
max-doc-length = 88
max-line-length = 120  # Set higher than line-length for E501 tolerance
ignore-overlong-task-comments = false
```

### pyflakes

```toml
[tool.ruff.lint.pyflakes]
allowed-unused-imports = ["myapp.compat"]
```

## Format Settings

```toml
[tool.ruff.format]
quote-style = "double"              # "double" | "single" | "preserve"
indent-style = "space"              # "space" | "tab"
line-ending = "auto"                # "auto" | "lf" | "cr-lf" | "native"
skip-magic-trailing-comma = false
docstring-code-format = false
docstring-code-line-length = "dynamic"
preview = false
exclude = []
```

## Analyze Settings

```toml
[tool.ruff.analyze]
detect-string-imports = false
direction = "dependencies"          # "dependencies" | "dependents"
type-checking-imports = true
include-dependencies = {}
```

## Suppression Comments

```python
import os  # noqa: F401             # Line-level
# ruff: disable[E501]               # Block-level (0.15.0+)
# ruff: enable[E501]
# ruff: noqa: F401, E501            # File-level
# isort: skip_file                   # isort file skip
# isort: off / # isort: on           # isort block
# fmt: off / # fmt: on               # Format block
a = [1,2,3]  # fmt: skip            # Format skip (statement-level)
```

## Format Suppression in Markdown (Preview)

```markdown
<!-- fmt:off -->
<!-- fmt:on -->
<!-- blacken-docs:off -->
<!-- blacken-docs:on -->
```

## isort Action Comments

```python
# isort: skip_file
# isort: off / # isort: on
# isort: skip          # Skip next import
# isort: split         # Force section break
# ruff: isort: skip_file  # Ruff-prefixed variant
```
