# Patterns

Typhon supports powerful pattern matching in various contexts, including `let`/`var` declarations, `match` statements, `for` loops, `with` statements, and `if-let` constructs.

## Tuple Patterns

Tuple patterns match tuples specifically. They are distinguished from general sequence patterns by using parentheses `()`.

```typhon
let (x, y) = (1, 2)
```

This pattern matches a tuple of exactly two elements. It will **not** match a list or other sequences, unlike Python's behavior where tuples and lists are often interchangeable in patterns.

Note: In a `match` statement, `case (x, y)` is equivalent to `case ((x, y))`. The parentheses around the pattern in `case` are part of the syntax, but if the pattern itself is a tuple, the extra parentheses are optional.

## Sequence Patterns

Sequence patterns match any sequence (lists, tuples, etc.) and use square brackets `[]`.

```typhon
let [x, y] = [1, 2]
let [head, *tail] = (1, 2, 3) # Matches a tuple too
```

**Note on Matching Order:** Since sequence patterns `[...]` match both lists and tuples, you must be careful with the order of patterns in a `match` statement if you want to distinguish them.

```typhon
match ((1, 2)) {
    case ([x, y]) { print("Matched sequence") } # Matches the tuple!
    case (x, y) { print("Matched tuple") }    # Unreachable
}

# To distinguish, place the specific tuple pattern first:
match ((1, 2)) {
    case (x, y) { print("Matched tuple") }
    case ([x, y]) { print("Matched sequence") }
}
```

## Attribute Patterns

Attribute patterns allow you to match against the attributes of an object. This is similar to class patterns but focuses on the structure (attributes) rather than the class type itself. The syntax uses curly braces with dot-prefixed keys `{.key}`.

```typhon
# Simple capture
let {.x, .y} = point

# Renaming and Type Annotations
let {.x = a: int, .y = b: str} = obj
```

In the second example:
- The attribute `x` of `obj` is matched and bound to variable `a`, which is expected to be an `int`.
- The attribute `y` of `obj` is matched and bound to variable `b`, which is expected to be a `str`.

## Capture Patterns & Type Annotations

You can bind values to variables using capture patterns. Typhon allows you to add type annotations to **any** captured variable in a pattern, modifying standard Python.

```typhon
match (val) {
    case (x: int, y: str) { ... }
    case [head: int, *tail: list[int]] { ... }
}
```

## Other Patterns

Typhon also supports standard patterns found in Python:

- **Literal Patterns**: Match exact values (e.g., `1`, `"hello"`, `True`).
- **Class Patterns**: Match against a class and its attributes (e.g., `Point(x=1, y=2)`).
- **As Patterns**: Bind a matched value to a name (e.g., `case [x, y] as p`).
- **Or Patterns**: Match one of multiple patterns (e.g., `case 0 | 1`).
- **Wildcard Pattern**: `_` matches anything but does not bind it.
- **Rest Patterns**: `*rest` matches the remaining elements in a sequence.
