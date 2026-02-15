# Operators

## Logical Operators

Typhon uses C-style logical operators, while Python keyword forms remain reserved.

- `&&`: Logical AND
- `||`: Logical OR
- `!`: Logical NOT

```typhon
if (x > 0 && y < 10) { ... }
```

`&&` and `||` short-circuit.

## Precedence Notes

See the complete table in [Operator Precedence](precedence.md).

Key points:

- Unary `!` (stronger than arithmetic operators)
- Arithmetic and bitwise operators (standard order)
- `&&`
- `||`
- `??` (weaker than `||`)
- `|>`, `?|>` (weaker than `??`; left-associative)

For `?.`, `?[]`, and `?()`, precedence is the same as the non-optional forms (`.`, `[]`, `()`).

## Arithmetic Operators

Standard arithmetic operators are supported: `+`, `-`, `*`, `/`, `//`, `%`, `**`.

## Comparison Operators

Standard comparison operators are supported: `==`, `!=`, `<`, `>`, `<=`, `>=`, `is`, `is not`, `in`, `not in`.

## Assignment Operators

- `=`: Assignment
- `+=`, `-=`, `*=`, `/=`, etc.: Augmented assignment.
