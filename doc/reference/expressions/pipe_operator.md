# Pipe Operator

The pipe operator `|>` passes the left value as the first argument of the right call.

```typhon
x |> f  # Equivalent to f(x)
```

It is left-associative.

`|>` and `?|>` have low precedence (weaker than `??`, `||`, `&&`, comparisons, and arithmetic operators).

```typhon
data |> process |> save
# Equivalent to save(process(data))
```

```typhon
x + 1 |> f
# Equivalent to f(x + 1)

x ?? y |> f
# Equivalent to f(x ?? y)
```

## Optional Pipe (`?|>`)

The optional pipe operator evaluates the right side only when the left-hand side is not `None`.

```typhon
maybe_val ?|> process
# Equivalent to: process(maybe_val) if maybe_val is not None else None
```

`?|>` is also left-associative and uses the same precedence as `|>`.
