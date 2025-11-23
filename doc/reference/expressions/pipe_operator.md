# Pipe Operator

The pipe operator `|>` allows you to pass the result of an expression as the first argument to a function.

```typhon
x |> f  # Equivalent to f(x)
```

It is left-associative and has low precedence.

```typhon
data |> process |> save;
# Equivalent to save(process(data))
```

## Optional Pipe (`?|>`)

The optional pipe operator calls the function only if the left-hand side is not `None`.

```typhon
maybe_val ?|> process
# Equivalent to: process(maybe_val) if maybe_val is not None else None
```
