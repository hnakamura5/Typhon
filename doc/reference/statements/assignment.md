# Assignment

Assignment binds a value to an existing mutable target. Declarations use `let` or `var`.

Bindings declared by `let` are immutable and cannot be reassigned.

## Simple Assignment


```typhon
var x = 1
x = 2
```

## Augmented Assignment

Typhon supports standard augmented assignments.

```typhon
var x = 1
x += 1
```

## Destructuring Assignment

Typhon supports destructuring for tuples and lists. This is a form of **pattern matching** (see [Patterns](patterns.md)).

Note that for variable declarations (`let`/`var`) with refutable patterns (patterns that might fail), you must use the `let-else` syntax (see [Variables](../variables.md)). For simple assignments to existing variables, standard pattern matching rules apply.

```typhon
let (a, b) = (1, 2)
let [x, *y] = [1, 2, 3] else {
    print("Failed to match list")
    raise ValueError("Failed to match list")
}
let {.x, .y} = {|x = 10, y = 20|}
```

Note: Chained assignments `a = b = c` are forbidden.
