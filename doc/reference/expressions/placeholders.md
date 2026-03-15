# Placeholders

The underscore `_` can act as a placeholder to build anonymous functions concisely.

```typhon
let inc = _ + 1
# Equivalent to: (x) => x + 1
```

## Boundary summary

Placeholder conversion targets the largest expression that contains `_`, but not only `_`.

Note the boundaries below limit the conversion inside them:

- Call: `f(_ + 1)` is `f((x) => x + 1)`
  - (is not `(x) => f(x + 1)`)
- Pipe: `v |> f(_)` is `v |> ((x) => f(x))`
  - (is not `(x) => v |> f(x)`)
- Function-literal body: `(x) => f(x, _)` is `(x) => ((y) => f(x, y))`
  - (is not `(y) => (x) => f(x, y)`)

## Examples

- An expression containing `_` becomes a function.

```typhon
let inc = _ + 1
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

- Boundary-sensitive behavior:

```typhon
f(_ + 1)           # f((x) => x + 1)
f(g(_))            # f((x) => g(x))
v |> f(_)          # v |> ((x) => f(x))
(x + 1) |> (_ * 2) # (x + 1) |> ((y) => y * 2)
```

## Placeholder and boundary rules in detail

`_` is interpreted by syntactic context:

- In left-hand-side contexts (assignment targets, `match`/`case` patterns, import bindings), `_` is a wildcard pattern.
- In all other contexts, `_` is a placeholder expression.

The "largest" expression containing `_` (but not only `_`) is converted into an anonymous function. Here, "largest" is limited by the innermost **boundary**:

- **Function Calls:** Both the callee and the arguments act as boundaries.
  - Example: `f(_ + 1)` becomes `f((x) => x + 1)`.
  - Example: `f(g(_))` becomes `f((x) => g(x))`. Here, `_` alone is not converted to function; the surrounding expression `g(_)` is the target.
- **Pipe Operators:** Both operands of a pipe `|>` act as boundaries.
  - Example: `f(_) |> g(_)` becomes ` ((x) => f(x))|> ((y) => g(y))`.
- **Function Literals:** The body of a function literal acts as a boundary.
  - Example: `(x) => f(x, _)` becomes `(x) => ((y) => f(x, y))`.
