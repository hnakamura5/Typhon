# Placeholders

The underscore `_` can be used as a placeholder to create anonymous functions concisely.

```typhon
let add_one = _ + 1
# Equivalent to: (x) => x + 1
```

## Examples

- The expression containing `_` becomes a function.

```typhon
let add1 = _ + 1
# Equivalent to: (x) => x + 1
```

- Multiple `_` placeholders create a function with multiple arguments, assigned from left to right.

```typhon
let add = _ + _
# Equivalent to: (x, y) => x + y
```

- Sole `_` is not converted to function.

```typhon
let x = _
# Syntax error
```

- Boundaries: The function scope is determined by the innermost "boundary" (function call, pipe, or explicit lambda).

```typhon
f(_ + 1)      # f((x) => x + 1)
f(g(_))       # f((x) => g(x))
v |> f(_)     # v |> ((x) => f(x))
```

## Rules in Detail

The smallest expression containing a placeholder `_` (but not consisting solely of `_`) is converted into an anonymous function. The scope of this function is determined by the innermost **boundary**, defined as follows:

- **Function Calls:** Both the callee and the arguments act as boundaries.
  - Example: `f(_ + 1)` becomes `f((x) => x + 1)`.
  - Example: `f(g(_))` becomes `f((x) => g(x))`. Here, `_` alone is not converted to function; the surrounding expression `g(_)` is the target.
- **Pipe Operators:** Both operands of a pipe `|>` act as boundaries.
  - Example: `v |> f(_)` becomes `v |> ((x) => f(x))`.
- **Function Literals:** The body of a function literal acts as a boundary.
  - Example: `(x) => f(x, _)` becomes `(x) => ((y) => f(x, y))`.
