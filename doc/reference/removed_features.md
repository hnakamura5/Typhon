# Removed Features

Typhon removes some Python features to keep scoping and control flow explicit.

## Removed Keywords

- `del`: Variable deletion is not supported. Use scope exit for cleanup.
- `global`: Global variable modification is not supported.
- `nonlocal`: Modification of outer scope variables is not supported (except for mutable objects).
- `lambda`: Replaced by arrow functions `(x) => x`.

## Removed Syntax

- **Wildcard imports**: `from module import *` is forbidden to prevent namespace pollution.
- **Chained Assignment**: `a = b = c` is forbidden. Use separate assignments.
- **Tuple Unpacking Assignment without Parentheses**: `a, b = 1, 2` is invalid. Use `(a, b) = (1, 2)`.
- **If Expression**: `x if cond else y` is forbidden. Use `(if (cond) x else y)`.
- **Control Statements in Class Body**: Only declarations (`let`, `var`, `def`) are allowed in class bodies.
- **Dead code**: Code after scope-exiting statements is forbidden.

## Rationale

These removals are intended to:

- Simplify the language.
- Make control flow and data flow more explicit.
- Prevent common errors associated with dynamic scoping and side effects.
