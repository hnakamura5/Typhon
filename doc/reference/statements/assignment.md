# Assignment

Assignment binds a value to one existing mutable variable name. Declarations use `let` or `var`.

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

## Assignment Restrictions

Reassignment is only allowed to individual existing variables.

- Pattern assignment on reassignment is forbidden.
- `else` cannot be attached to reassignment.

```typhon
var x = 1
x = 2 # OK

# (a, b) = (1, 2)          # Error: pattern reassignment is forbidden
# x = 1 else { return }     # Error: `else` is not allowed on reassignment
```

Note: Chained assignments `a = b = c` are forbidden.
