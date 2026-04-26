# ty Type System Feature Matrix

## Fully Implemented

### Special Types

`Any`, `None`, `NoReturn`/`Never`, `Literal[...]`, `LiteralString`, `type[C]`, `float`/`complex` promotion, `Final`, `@final`, `ClassVar`, `Annotated`, `Required`/`NotRequired`/`ReadOnly`, `Union`/`Optional`

### Generics

`TypeVar` (legacy + PEP 695 syntax), bounds, constraints, defaults, variance, `ParamSpec` (+ `.args`/`.kwargs`, defaults), `Self`, generic classes/functions/aliases

### Protocols

Definition, generic protocols, structural subtyping, inheritance, `@runtime_checkable`, `@property` members (partial)

### Type Narrowing

`isinstance()`/`issubclass()`, `is None`/`is not None`, identity checks, truthiness, `assert`, `match` statements, `hasattr()`, `callable()`, assignment, `TypeIs`/`TypeGuard`

### Tuples

Heterogeneous, homogeneous, empty, mixed, indexing, slicing, subclasses, unpacking

### NamedTuple

Class syntax, field access, defaults, read-only, inheritance, functional syntax

### TypedDict

Class syntax, key access, `Required`/`NotRequired`/`ReadOnly`, inheritance, generic, recursive, structural assignability

### Enums

`Enum`/`IntEnum`/`StrEnum`, `Literal[Member]`, `.name`/`.value` inference, `auto()`, `member()`/`nonmember()`, exhaustiveness checking

### Callables

`Callable[[X, Y], R]`, gradual form, `ParamSpec`, callback protocols, assignability

### Overloads

Resolution, generic, methods/constructors/static/classmethod

### Dataclasses

All decorator params, `field()`, `InitVar`, `ClassVar`, `KW_ONLY`, `replace()`, `asdict()`, inheritance, generic

## Unique to ty

| Feature                         | Description                                                         |
| ------------------------------- | ------------------------------------------------------------------- |
| **Intersection types**          | First-class `A & B` — not available in mypy or pyright              |
| **Unknown vs Any**              | Explicit gradual typing: `Any` is deliberate, `Unknown` is inferred |
| **Fixpoint iteration**          | Handles cyclic type dependencies                                    |
| **Reachability analysis**       | Detects unreachable code across version-specific branches           |
| **Fine-grained incrementality** | Change one function -> only re-analyze that function + dependents   |

## Not Yet Implemented

| Feature                                         | Impact                      | Tracking |
| ----------------------------------------------- | --------------------------- | -------- |
| `TypeVarTuple` / `Unpack`                       | NumPy/tensor typing         | #156     |
| `Concatenate`                                   | Supported in current beta   | —        |
| `type[SomeProtocol]`                            | Protocol metaclass          | #903     |
| `@classmethod`/`@staticmethod` protocol members | Protocol completeness       | #1381    |
| `ClassVar` protocol members                     | Protocol completeness       | #1380    |
| TypedDict functional syntax                     | `TD = TypedDict("TD", ...)` | #3095    |
| PEP 728 `closed`/`extra_items` TypedDict        | TypedDict completeness      | #3096    |
| `Unpack` for `**kwargs`                         | Typed kwargs                | #1746    |
| Tuple length narrowing                          | Tuple refinement            | #560     |
| Enum functional syntax + `Flag`                 | Enum completeness           | #876     |
| Overlapping overload diagnostics                | Overload correctness        | #103     |
| `dataclass_transform`                           | Partial                     | —        |
| Tagged union narrowing for TypedDict            | Discriminated unions        | #1479    |

## Key Rules

| Rule                            | Default | Description                           |
| ------------------------------- | ------- | ------------------------------------- |
| `unresolved-import`             | error   | Module not found                      |
| `unresolved-attribute`          | error   | Attribute not found on type           |
| `invalid-assignment`            | error   | Type mismatch in assignment           |
| `invalid-argument-type`         | error   | Wrong argument type                   |
| `invalid-return-type`           | error   | Return type mismatch                  |
| `possibly-unresolved-reference` | warn    | May not be defined in all paths       |
| `division-by-zero`              | ignore  | Literal division by zero              |
| `redundant-cast`                | warn    | Unnecessary cast() call               |
| `invalid-method-override`       | error   | Override breaks Liskov substitution   |
| `possibly-missing-attribute`    | warn    | Attribute may not exist (union types) |
