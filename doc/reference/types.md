# Types

Typhon is a statically typed language. It supports Python's basic types and extends them with new constructs.

## Basic Types

- `int`
- `float`
- `bool`
- `str`
- `bytes`
- `None` (Unit type)

## Collection Types

### Tuples

Typhon introduces a dedicated syntax for tuple types: `(T1, T2, ...)`.

```typhon
let x: (int, str) = (1, "hello")
```

### Lists

List types are denoted as `[T]`.

```typhon
let numbers: [int] = [1, 2, 3]
```

## Optional Types

Optional types are written as `T?`, which is equivalent to `T | None`.

```typhon
let maybe_int: int? = None
```

## Function Types

Arrow syntax is used for function types: `(ArgType1, ArgType2) -> ReturnType`.

```typhon
let adder: (int, int) -> int = (x, y) => x + y
```

### Translation

This is syntactic sugar for `Protocol`.

```python
class MyProtocol(Protocol):
    def __call__(self, x1: int, x2: int) -> int: ...
```

## Data Record Types

[Data records](./expressions/literals.md#data-record-literals) are anonymous immutable data structures, similar to anonymous dataclasses.

```typhon
let point: {|x: int, y: str|} = {|x = 10, y = "20"|}
```

### Translation

This is translated to a `Protocol` of a dataclass.

```python
@dataclass(frozen=True, repr=False, unsafe_hash=True)
class AnonRecord(Protocol):
    x: int
    y: str
```

