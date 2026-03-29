# Ruff Rule Catalog (v0.15.8 — 954 Rules, 57 Categories)

817 stable, 137 preview. 237 always fixable, 229 sometimes fixable, 488 not fixable.

## Framework-Specific

| Prefix | Linter | Rules | Fixable | Focus |
|--------|--------|------:|--------:|-------|
| AIR | Airflow | 10 | 5 | DAG args, Airflow 3 migration |
| DJ | flake8-django | 7 | 0 | Model/form anti-patterns |
| FAST | FastAPI | 3 | 3 | Route/dependency issues |
| NPY | NumPy-specific | 4 | 3 | Deprecated APIs, legacy random |
| PD | pandas-vet | 13 | 1 | `.inplace`, `.values`, etc. |

## Core Python

| Prefix | Linter | Rules | Fixable | Focus |
|--------|--------|------:|--------:|-------|
| E/W | pycodestyle | 67 | 46 | PEP 8 style |
| F | Pyflakes | 43 | 11 | Undefined names, unused imports |
| N | pep8-naming | 16 | 2 | Naming conventions |
| D | pydocstyle | 47 | 30 | Docstring conventions |
| DOC | pydoclint | 7 | 0 | Docstring/signature mismatches (all preview) |
| UP | pyupgrade | 47 | 46 | Version upgrade opportunities |
| I | isort | 2 | 2 | Import sorting |
| C90 | mccabe | 1 | 0 | Cyclomatic complexity |

## Pylint Re-implementations (115 rules total)

| Prefix | Category | Rules | Fixable |
|--------|----------|------:|--------:|
| PLC | Convention | 16 | 7 |
| PLE | Error | 38 | 10 |
| PLR | Refactor | 33 | 13 |
| PLW | Warning | 28 | 9 |

## Flake8 Plugin Re-implementations

| Prefix | Linter | Rules | Fixable | Focus |
|--------|--------|------:|--------:|-------|
| A | flake8-builtins | 6 | 0 | Shadowing built-in names |
| ANN | flake8-annotations | 11 | 5 | Missing type annotations |
| ARG | flake8-unused-arguments | 5 | 0 | Unused function arguments |
| ASYNC | flake8-async | 15 | 3 | Blocking calls in async |
| B | flake8-bugbear | 43 | 13 | Bug patterns, design issues |
| BLE | flake8-blind-except | 1 | 0 | Bare `except:` |
| C4 | flake8-comprehensions | 19 | 18 | Unnecessary comprehensions |
| COM | flake8-commas | 3 | 2 | Trailing commas |
| CPY | flake8-copyright | 1 | 0 | Copyright headers (preview) |
| DTZ | flake8-datetimez | 10 | 0 | Naive datetime usage |
| EM | flake8-errmsg | 3 | 3 | String literals in exceptions |
| EXE | flake8-executable | 5 | 1 | Shebang/permission issues |
| FA | flake8-future-annotations | 2 | 2 | `from __future__ import annotations` |
| FBT | flake8-boolean-trap | 3 | 0 | Boolean positional arguments |
| FIX | flake8-fixme | 4 | 0 | TODO/FIXME/XXX/HACK |
| G | flake8-logging-format | 8 | 2 | Logging format issues |
| ICN | flake8-import-conventions | 3 | 1 | Unconventional aliases |
| INP | flake8-no-pep420 | 1 | 0 | Missing `__init__.py` |
| INT | flake8-gettext | 3 | 0 | i18n/gettext patterns |
| ISC | flake8-implicit-str-concat | 4 | 3 | Implicit string concat |
| LOG | flake8-logging | 7 | 5 | Logging misuse |
| PIE | flake8-pie | 8 | 7 | Misc code smells |
| PT | flake8-pytest-style | 31 | 13 | pytest best practices |
| PTH | flake8-use-pathlib | 35 | 28 | `os.path` -> pathlib |
| PYI | flake8-pyi | 55 | 29 | Type stub issues |
| Q | flake8-quotes | 5 | 5 | Quote consistency |
| RET | flake8-return | 8 | 8 | Return patterns |
| RSE | flake8-raise | 1 | 1 | Unnecessary parens in raise |
| S | flake8-bandit | 73 | 0 | Security issues |
| SIM | flake8-simplify | 30 | 26 | Simplification opportunities |
| SLF | flake8-self | 1 | 0 | Private member access |
| SLOT | flake8-slots | 3 | 0 | Missing `__slots__` |
| T10 | flake8-debugger | 1 | 0 | Debugger imports |
| T20 | flake8-print | 2 | 2 | `print()` statements |
| TC | flake8-type-checking | 9 | 8 | TYPE_CHECKING optimization |
| TD | flake8-todos | 7 | 1 | TODO format |
| TID | flake8-tidy-imports | 4 | 2 | Banned/relative imports |

**Note:** `TCH` is a legacy alias for `TC`. Both work, prefer `TC` in new configs.

## Other Tool Re-implementations

| Prefix | Linter | Rules | Fixable | Replaces |
|--------|--------|------:|--------:|----------|
| ERA | eradicate | 1 | 0 | Commented-out code detection |
| FLY | flynt | 1 | 1 | f-string conversion |
| FURB | refurb | 36 | 36 | Code modernization (all fixable) |
| PGH | pygrep-hooks | 5 | 2 | Blanket type: ignore, eval |
| PERF | Perflint | 6 | 4 | Performance anti-patterns |
| TRY | tryceratops | 10 | 2 | Exception handling |
| YTT | flake8-2020 | 10 | 0 | sys.version comparison |

## Ruff-Specific (73 rules)

| Code | Name | Notable |
|------|------|---------|
| RUF100 | Unused `# noqa` directive | The "yesqa replacement" |
| RUF102 | Invalid rule code in suppression | New in 0.15.0 |
| RUF103 | Invalid suppression comment syntax | New in 0.15.0 |
| RUF104 | Unmatched suppression comment | New in 0.15.0 |
| RUF060 | `in` against empty collection | Stabilized 0.15.0 |
| RUF037 | Unnecessary empty iterable | |

## Rules Stabilized in Recent Releases

### 0.15.0 (Feb 2026)
ASYNC212/240/250 (blocking calls in async), B912 (map without strict), UP042 (replace StrEnum), FURB110/171, RUF060/061/064, RUF102-104

### 0.13.0 (Sep 2025)
AIR002/301/302/311/312 (Airflow 3 migration), UP050, FURB116, RUF043/059

### 0.12.0 (Jul 2025)
UP045/046/047/049 (PEP 604/695 syntax), PLR1733, PLW0177/1641, FURB122/132/157/162/166, RUF028/049/053/057/058

## Conflicting Rule Pairs

| Pair | Resolution |
|------|-----------|
| D203 vs D211 | Choose D211 (no blank line before class docstring) |
| D212 vs D213 | Choose D212 (docstring starts on first line) |
| COM812 vs formatter | Disable COM812 when using ruff format |
| ISC001 vs formatter | Only conflicts with specific ISC002 + allow-multiline settings |
