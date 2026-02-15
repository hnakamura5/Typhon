# Patterns

Typhon supports powerful pattern matching in various contexts, including `let`/`var` declarations, `match` statements, `for` loops, `with` statements, and `if-let` constructs.

## Tuple Patterns

Tuple patterns match tuples specifically. They use parentheses `()`.

```typhon
let (x, y) = (1, 2)
```

This pattern matches a tuple of exactly two elements. It does **not** match lists or other sequences.

Note: In `match`, `case (x, y)` is equivalent to `case ((x, y))`. Outer parentheses are syntax; tuple parentheses belong to the pattern.

## Sequence Patterns

Sequence patterns use square brackets `[]` and match sequences (lists, tuples, etc.).

```typhon
let [x, y] = [1, 2]
let [head, *tail] = (1, 2, 3) # Matches a tuple too
```

**Note on matching order:** Because `[...]` can match both lists and tuples, order matters when you need to distinguish them in `match`.

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

Attribute patterns match object attributes by structure, not class type. Syntax uses dot-prefixed keys in braces (`{.key}`).

```typhon
# Simple capture
let {.x, .y} = point

# Renaming and Type Annotations
let {.x = a: int, .y = b: str} = obj
```

In the second example, `obj.x` is captured as `a: int` and `obj.y` as `b: str`.

## Capture Patterns & Type Annotations

Capture patterns bind values to variables. Typhon allows type annotations on **any** captured variable in a pattern.

```typhon
match (val) {
    case (x: int, y: str) { ... }
    case [head: int, *tail: [int]] { ... }
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
