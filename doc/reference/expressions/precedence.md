# Operator Precedence

This page defines Typhon operator precedence from stronger to weaker.

## Rule of compatibility

- For operators shared with Python, Typhon keeps Python precedence and associativity.
- Typhon-specific updates are integrated into the same order below (`&&`, `||`, `?`-family, `|>`, `?|>`).

## Precedence table (stronger -> weaker)

| Level | Operators / forms | Associativity | Notes |
| --- | --- | --- | --- |
| 1 | Primary forms: `x.y`, `x?.y`, `x(...)`, `x?(...)`, `x[...]`, `x?[...]` | left | Same level as normal attribute/call/subscript. |
| 2 | `await x` | right | Same as Python `await` expression position. |
| 3 | Prefix unary: `+x`, `-x`, `~x`, `!x` | right | `!` is logical NOT in Typhon. |
| 4 | Postfix optional/unwrap: `x?`, `x!` | left | Postfix null-safety operators. |
| 5 | `**` | right | Same as Python exponentiation. |
| 6 | `*`, `@`, `/`, `//`, `%` | left | Same as Python multiplicative level. |
| 7 | `+`, `-` | left | Same as Python additive level. |
| 8 | `<<`, `>>` | left | Same as Python shifts. |
| 9 | `&` | left | Same as Python bitwise AND. |
| 10 | `^` | left | Same as Python bitwise XOR. |
| 11 | `\|` | left | Same as Python bitwise OR. |
| 12 | Comparisons: `<`, `<=`, `>`, `>=`, `==`, `!=`, `is`, `is not`, `in`, `not in` | chain | Same as Python comparison chaining. |
| 13 | `&&` | left | Typhon logical AND (`and` equivalent). |
| 14 | `\|\|` | left | Typhon logical OR (`or` equivalent). |
| 15 | `??` | left | Null-coalescing. Weaker than `\|\|`. |
| 16 | `\|>`, `?\|>` | left | Pipe operators. Weaker than `??`. |

## Quick examples

```typhon
x + 1 |> f
# Equivalent to f(x + 1)

x || y ?? z |> g
# Equivalent to g((x || y) ?? z)

x |> f |> g |> h
# Equivalent to h(g(f(x)))
```

## Related

- [Operators](operators.md)
- [Null Safety](null_safety.md)
- [Pipe Operator](pipe_operator.md)
