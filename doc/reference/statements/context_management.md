# Context Management

Typhon uses this syntax convention:

- Use parentheses when the header binds names for a new braced inner scope.
- Omit parentheses when binding into the current scope.

This convention is general across language forms, not only `with`.

## With Statement

Use `with` for resource management.

```typhon
with (let f = open("file.txt")) {
    f.read()
}
```

## Inline With

Typhon also supports inline `with`, which applies to the rest of the current scope.

```typhon
if (True) {
    with let f = open("file.txt")
    f.read()
} # f is closed here
```

`with (let ...) { ... }` binds for the braced block. `with let ...` binds in the current scope.
