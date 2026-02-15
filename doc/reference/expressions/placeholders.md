# Placeholders

The underscore `_` can act as a placeholder to build anonymous functions concisely.

```typhon
let add_one = _ + 1
# Equivalent to: (x) => x + 1
```

## Examples

- An expression containing `_` becomes a function.

```typhon
let add1 = _ + 1
# Equivalent to: (x) => x + 1
```

- Multiple `_` placeholders create a function with multiple parameters, assigned left to right.

```typhon
let add = _ + _
# Equivalent to: (x, y) => x + y
```

- A standalone `_` is not converted into a function.

```typhon
let x = _
# Syntax error
```

- Boundaries: Function scope is determined by the innermost boundary (function call, pipe, or function literal).

```typhon
f(_ + 1)      # f((x) => x + 1)
f(g(_))       # f((x) => g(x))
v |> f(_)     # v |> ((x) => f(x))
```

## Rules in Detail

`_` is interpreted by syntactic context:

- In left-hand-side contexts (assignment targets, `match`/`case` patterns, import bindings), `_` is a wildcard pattern.
- In all other contexts, `_` is a placeholder expression.

The smallest expression containing `_` (but not only `_`) is converted into an anonymous function. The function scope is determined by the innermost **boundary**:

- **Function Calls:** Both the callee and the arguments act as boundaries.
  - Example: `f(_ + 1)` becomes `f((x) => x + 1)`.
  - Example: `f(g(_))` becomes `f((x) => g(x))`. Here, `_` alone is not converted to function; the surrounding expression `g(_)` is the target.
- **Pipe Operators:** Both operands of a pipe `|>` act as boundaries.
  - Example: `v |> f(_)` becomes `v |> ((x) => f(x))`.
- **Function Literals:** The body of a function literal acts as a boundary.
  - Example: `(x) => f(x, _)` becomes `(x) => ((y) => f(x, y))`.
