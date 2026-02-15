# Literals

## Basic Literals

Basic literals follow Python:

- **Integers**: `1`, `42`, `-5`
- **Floats**: `1.0`, `3.14`, `-0.01`
- **Strings**: `"hello"`, `'world'`
- **Booleans**: `True`, `False`
- **None**: `None`

### F-Strings

Typhon supports Python-style f-strings:

```typhon
let name = "World"
let greeting = f"Hello, {name}!"
print(greeting) # Hello, World!

let x = 10
let y = 20
print(f"{x} + {y} = {x + y}") # 10 + 20 = 30
```

F-strings can contain expressions and format specifiers:

```typhon
let pi = 3.14159
print(f"Pi is approximately {pi:.2f}") # Pi is approximately 3.14
```

## Collection Literals

Collection literals follow Python:

- **Lists**: `[1, 2, 3]`
- **Tuples**: `(1, "a")`
- **Dictionaries**: `{"a": 1, "b": 2}`
- **Sets**: `{1, 2, 3}`

## Function Literals

Function literals (arrow functions) provide concise anonymous function syntax. Unlike Python `lambda`, they can contain multiple statements.

### Single-Expression Form

For single-expression functions:

```typhon
let add = (x, y) => x + y
let square = (n) => n * n
let greet = (name) => f"Hello, {name}!"
```

### Block Form

For multi-statement functions, use braces:

```typhon
let process = (x) => {
    let doubled = x * 2
    let result = doubled + 10
    return result
}
```

### With Type Annotations

Function literals support type annotations:

```typhon
let add: (int, int) -> int = (x: int, y: int) -> int => x + y

let validate = (value: str) -> bool => {
    if (len(value) > 0) {
        return True
    }
    return False
}
```

Function literals have the same capabilities as `def` functions, including closure capture.

## Data Record Literals

Data records are anonymous immutable objects.

```typhon
let record = {|x = 10, y = "20"|}
print(record.x)
```

Their type form is `{|x: int, y: str|}`.

### Translation

The literal `{|x = 10, y = "20"|}` is translated into an instantiation of an anonymous immutable dataclass.

```python
@dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class AnonRecord:
    x: int
    y: str

AnonRecord(x=10, y="20")
```
