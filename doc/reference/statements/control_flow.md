# Control Flow

## If Statement

Standard `if`, `elif`, `else` structure. Parentheses around the condition are required.

```typhon
if (x > 0) {
    print("Positive")
} elif (x < 0) {
    print("Negative")
} else {
    print("Zero")
}
```

## If-Let Statement

`if-let` combines a check for `None` (or pattern matching) with a conditional block.

```typhon
if (let x = maybe_val()) {
    # Executed if maybe_val() is not None
    # x is bound to the value
    print(x)
}
```

It supports additional conditions and pattern matching:

```typhon
if (let x = f(); x > 0) { ... }
if (let [1, x] = get_list()) { ... }
```

## Let-Else Statement

`let-else` allows for refutable pattern matching where the failure case must diverge (exit the scope). This is useful for flattening nested `if-let` structures (guard clauses).

```typhon
let Some(x) = maybe_val else {
    return # Must return, break, continue, or raise
}
# x is available here
print(x)
```

## Match Statement

Pattern matching with `match` and `case`.

```typhon
match (val) {
    case (0) { print("Zero") }
    case (x) if (x > 0) { print("Positive") }
    case (_) { print("Other") }
}
```

## While Loop

Standard `while` loop.

```typhon
while (x > 0) {
    x -= 1
}
```

## For Loop

Iterate over iterables.

```typhon
for (let x in range(10)) {
    print(x)
}
```

## Break and Continue

Standard `break` and `continue` statements are supported.
