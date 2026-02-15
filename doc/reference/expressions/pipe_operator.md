# Pipe Operator

The pipe operator `|>` passes the left value as the first argument of the right call.

```typhon
x |> f  # Equivalent to f(x)
```

It is left-associative with low precedence.

```typhon
data |> process |> save
# Equivalent to save(process(data))
```

## Optional Pipe (`?|>`)

The optional pipe operator evaluates the right side only when the left-hand side is not `None`.

```typhon
maybe_val ?|> process
# Equivalent to: process(maybe_val) if maybe_val is not None else None
```
