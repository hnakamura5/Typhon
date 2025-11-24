# Placeholders

The underscore `_` can be used as a placeholder to create anonymous functions concisely.

```typhon
let add_one = _ + 1
# Equivalent to: (x) => x + 1
```

## Rules

- The expression containing `_` becomes a function.
- Multiple `_` placeholders create a function with multiple arguments, assigned from left to right.

```typhon
let add = _ + _
# Equivalent to: (x, y) => x + y
```

- Boundaries: The function scope is determined by the innermost "boundary" (function call, pipe, or explicit lambda).

```typhon
f(_ + 1)      # f((x) => x + 1)
f(g(_))       # f((x) => g(x))
v |> f(_)     # v |> ((x) => f(x))
```
