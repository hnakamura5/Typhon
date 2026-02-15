# Control Flow

## If Statement

Standard `if`/`elif`/`else` structure. Parentheses around conditions are required.

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

`if-let` combines pattern binding with a conditional block.

```typhon
if (let x = maybe_val()) {
    # Executed if maybe_val() is not None
    # x is bound to the value
    print(x)
}
```

It also supports additional conditions and patterns:

```typhon
if (let x = f(); x > 0) { ... }
if (let [1, x] = get_list()) { ... }
```

## Let-Else Statement

`let-else` supports refutable pattern matching where the failure case must diverge (exit the scope). This is useful for guard-style code.

`let-else` binds variables in the current scope, so it uses no header parentheses.

```typhon
let [head, *tail] = values else {
    return # Must return, break, continue, or raise
}
# head and tail are available here
print(head)
```

## Match Statement

Pattern matching uses `match` and `case`. See [Patterns](patterns.md) for available pattern forms.

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
