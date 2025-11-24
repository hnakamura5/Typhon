# Literals

## Basic Literals

- **Integers**: `1`, `42`, `-5`
- **Floats**: `1.0`, `3.14`, `-0.01`
- **Strings**: `"hello"`, `'world'`
- **Booleans**: `True`, `False`
- **None**: `None`

## Collection Literals

- **Lists**: `[1, 2, 3]`
- **Tuples**: `(1, "a")`
- **Dictionaries**: `{"a": 1, "b": 2}`
- **Sets**: `{1, 2, 3}`

## Data Record Literals

Data records are anonymous immutable objects.

```typhon
let record = {|x = 10, y = 20|};
print(record.x);
```

They are typed as `{|x: int, y: int|}`.

### Translation

The literal `{|x = 10, y = 20|}` is translated into an instantiation of an anonymous immutable dataclass.

```python
@dataclass(frozen=True)
class AnonRecord:
    x: int
    y: int

AnonRecord(x=10, y=20)
```
