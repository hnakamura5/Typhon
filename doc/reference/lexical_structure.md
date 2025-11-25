# Lexical Structure

## Comments

Typhon also supports block comments that can be nested. This is useful for commenting out large blocks of code that may already contain comments.

```typhon
#( This is a block comment )#

#(
  Comments can be nested.
  #( Inner comment )#
)#
```

```typhon
  if (...#(in the middle)#&& ...) {
    x = #(
      multiple line #(
        and nested comment
    )#  is OK.)# 1
  }
```

Comments act as whitespace.

## Identifiers

Identifiers follow standard rules but with a few Typhon-specific restrictions:

- Identifiers starting with `_typh_` are reserved for internal use.

## Keywords

Typhon retains most Python keywords but adds and removes some.

### New/Changed Keywords

- `let`: Immutable variable declaration
- `var`: Mutable variable declaration
- `static`: Static member or compile-time construct
- `&&`, `||`, `!`: Logical operators (replacing `and`, `or`, `not` in most contexts, though `and`/`or`/`not` are still reserved)

### Forbidden Keywords

- `del`
- `global`
- `nonlocal`
- `lambda`

## Delimiters

Typhon uses a mix of braces and significant whitespace, but with stricter rules than Python.

- **Statement Termination**: Statements are terminated by a semicolon `;` or a newline.
- **Blocks**: Blocks are delimited by braces `{ ... }`.
- **Line Breaks**: Line breaks act as delimiters (end of statement) unless the statement is clearly incomplete.

### Line Break Rules

A line break is treated as **whitespace** (continuation) if it occurs:

1. **Just after**:
   - Operators (e.g., `+`, `-`, `.`, `=`, `?`, `:`, `=>`, `->`, `,`).
   - Open brackets (`(`, `[`, `{`).
   - Modifiers and decorators (`static`, `async`, `@`).
   - Statement keywords that expect a body or continuation (e.g., `class`, `def`, `if`, `elif`, `while`, `for`, `except`, `with`, `match`, `case`).
   - The closing parenthesis `)` of a control statement header (e.g., `if (cond)`).

2. **Just before**:
   - Operators (EXCEPT `@`, `await`).
   - Closing brackets (`}`, `]`, `)`).
   - Keywords that continue a statement (`elif`, `else`, `except`, `finally`, `case`).

In all other cases, a line break is treated as a **semicolon** (statement terminator).

Note especially that line breaks just after return like keywords (`return`, `yield`, `raise`, `break`, `continue`) are **delimiter**. Not treated as whitespace.

```typhon
let x = 1
+ 2 # Parsed as let x = 1 + 2;

if (x > 0)
{ # Parsed as block of if
    print(x)
}

def f() {
    yield
    g() # Parsed as yield; g();
}
```

### Dead Code

The dead codes after scope exiting statement (`return`, `raise`, `break`, `continue`) are always syntax error.

```typhon
return
2 # Syntax error
```
