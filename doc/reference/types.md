# Types

Typhon is statically typed. It supports Python base types and adds Typhon-specific type syntax.

## Basic Types

- `int`
- `float`
- `bool`
- `str`
- `bytes`
- `None` (Unit type)

## Collection Types

### Tuples

Tuple types use `(T1, T2, ...)`.

```typhon
let x: (int, str) = (1, "hello")
```

### Lists

List types use `[T]`.

```typhon
let numbers: [int] = [1, 2, 3]
```

## Optional Types

Optional types use `T?`, equivalent to `T | None`.

```typhon
let maybe_int: int? = None
```

## Function Types

Function types use arrow syntax: `(ArgType1, ArgType2) -> ReturnType`.

```typhon
let adder: (int, int) -> int = (x, y) => x + y
```

### Translation

This is syntactic sugar over `Protocol`.

```python
class MyProtocol(Protocol):
    def __call__(self, x1: int, x2: int) -> int: ...
```

## Data Record Types

[Data records](./expressions/literals.md#data-record-literals) are anonymous immutable structures, similar to anonymous dataclasses.

```typhon
let point: {|x: int, y: str|} = {|x = 10, y = "20"|}
```

### Translation

This is translated to a dataclass shape expressed as a `Protocol`.

```python
@dataclass(frozen=True, repr=False, unsafe_hash=True)
class AnonRecord(Protocol):
    x: int
    y: str
```

