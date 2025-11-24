# Exception Handling

## Try-Except

Handle exceptions using `try`, `except`, and `finally`.

```typhon
try {
    dangerous_op();
} except (ValueError as e) {
    print("Value error:", e);
} except {
    print("Unknown error");
} finally {
    cleanup();
}
```

`else` block is also supported, executed if no exception occurs.

## Raise

Raise exceptions using `raise`.

```typhon
raise ValueError("Invalid value");
```

`raise from` is also supported.

```typhon
raise RuntimeError("Wrap") from e;
```
