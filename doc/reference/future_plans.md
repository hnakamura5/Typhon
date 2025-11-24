# Future Plans and Work in Progress

This section outlines features that are planned, currently under development, or have known limitations.

## Temporal Restrictions

- **Type Inference for Function Literals**: Currently works only when the function body is a single expression.
- **Pattern Matching in Declarations**: `let`/`var` is planned to support full pattern matching. Currently, it only supports tuple/list unpacking.
- **Error Messages**: The column end of error messages is not yet precise.
- **Placeholder Type Annotation**: Type annotations for placeholder expressions (`_`) are not supported yet.

## Bundled Libraries

- **`typhon.traceback`**: A drop-in replacement for the builtin `traceback` module to provide traceback display in Typhon's syntax.

## Compile Time Control

Typhon plans to support `static if` and `static assert` for compile-time code control. These are intended for debugging, testing, versioning, and transportation, *not* for metaprogramming or optimization.

### Static If

```typhon
static if (VERSION >= 3.13) {
    # Code compiled only if version condition is met
}
```

`static if` does not introduce a new lexical scope.

### Static Assert

```typhon
static assert("ast_debug" in DEBUG_FLAGS);
```

Causes a compile error if the assertion fails.

### Compile Time Booleans

- `True`, `False`
- Logical operators
- `VERSION` conditions
- `DEBUG_FLAGS` checks
