# Migration Guide: mypy/pyright to ty

## Error Code Mapping

### mypy -> ty

| mypy code | ty rule | Notes |
|-----------|---------|-------|
| `import-not-found` | `unresolved-import` | |
| `attr-defined` | `unresolved-attribute` | |
| `arg-type` | `invalid-argument-type` | |
| `assignment` | `invalid-assignment` | |
| `return-value` | `invalid-return-type` | |
| `union-attr` | `possibly-missing-attribute` | |
| `override` | `invalid-method-override` | |
| `redundant-cast` | `redundant-cast` | |
| `name-defined` | `possibly-unresolved-reference` | |
| `call-arg` | `invalid-argument-type` | Merged with arg-type |

### pyright -> ty

| pyright code | ty rule |
|-------------|---------|
| `reportMissingImports` | `unresolved-import` |
| `reportGeneralClassIssues` | Various specific rules |
| `reportMissingTypeStubs` | `unresolved-import` |
| `reportOptionalMemberAccess` | `possibly-missing-attribute` |
| `reportReturnType` | `invalid-return-type` |
| `reportAssignmentType` | `invalid-assignment` |
| `reportArgumentType` | `invalid-argument-type` |

## Configuration Mapping

### mypy -> ty

| mypy option | ty equivalent |
|-------------|---------------|
| `python_version = "3.12"` | `environment.python-version = "3.12"` |
| `ignore_missing_imports = true` | `rules.unresolved-import = "ignore"` |
| `exclude = ["tests"]` | `src.exclude = ["tests/**"]` (glob patterns) |
| `check_untyped_defs = true` | Default behavior (always on) |
| `disallow_untyped_defs = true` | Use ruff ANN001/ANN201 |
| `strict = true` | No single flag; enable rules individually |
| `plugins = ["pydantic.mypy"]` | **Not supported** |
| `warn_unused_ignores = true` | Default behavior |
| `warn_redundant_casts = true` | `rules.redundant-cast = "warn"` (default) |
| Per-module overrides | `[[tool.ty.overrides]]` with file globs |

### pyright -> ty

| pyright option | ty equivalent |
|---------------|---------------|
| `pythonVersion = "3.12"` | `environment.python-version = "3.12"` |
| `pythonPlatform = "Linux"` | `environment.python-platform = "linux"` |
| `venvPath` / `venv` | `environment.python = ".venv"` |
| `include = ["src"]` | `src.include = ["src/**/*.py"]` |
| `exclude = ["tests"]` | `src.exclude = ["tests/**"]` |
| `executionEnvironments` | `[[tool.ty.overrides]]` |
| `typeCheckingMode = "strict"` | No equivalent; configure rules individually |
| `# pyright: ignore` | `# ty: ignore` |

### Suppression Comment Mapping

| Tool | Syntax |
|------|--------|
| mypy | `# type: ignore[error-code]` |
| pyright | `# pyright: ignore[reportCode]` |
| ty | `# ty: ignore[rule-name]` |

ty honors `# type: ignore` by default (configurable via `analysis.respect-type-ignore-comments`).

## Step-by-Step Migration

### Phase 1: Baseline (Day 1)

```bash
# Auto-suppress all current errors
ty check --add-ignore

# Verify it passes
ty check
```

This adds `# ty: ignore[...]` comments to every line with a type error, giving you a clean baseline.

### Phase 2: Parallel CI (Week 1-4)

```yaml
# Run both, ty as non-blocking
- run: mypy .
- run: ty check || true  # Non-blocking
```

Compare outputs. Note differences in diagnostics.

### Phase 3: Gradual Cleanup (Ongoing)

Remove `# ty: ignore` comments one module at a time. Fix the underlying type errors.

### Phase 4: Switch (When Ready)

Replace mypy with ty in CI as the blocking check. Remove mypy config.

## When to Migrate Now

- Pure Python projects with no mypy plugin dependencies
- Projects that need faster CI (10-60x speedup)
- Teams that want a better LSP experience
- New projects starting from scratch

## When to Wait

- Heavy Pydantic plugin usage (first-class support coming)
- Django/SQLAlchemy plugin dependencies
- Need for `TypeVarTuple` (NumPy/tensor typing)
- Production environments requiring battle-tested stability
