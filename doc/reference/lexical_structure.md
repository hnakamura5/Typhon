# Lexical Structure

## Comments

Typhon supports nested block comments. This is useful when commenting out code that already contains comments.

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

Comments are treated as whitespace.

## Identifiers

Identifiers mostly follow Python rules, with Typhon-specific restrictions:

- Names starting with `_typh_` are reserved for internal use.

## Keywords

Typhon keeps most Python keywords, but adds and forbids some forms.

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

Typhon uses braces and line breaks, with stricter continuation rules than Python.

- **Statement termination**: A statement ends at `;` or a newline.
- **Blocks**: Blocks are delimited by braces `{ ... }`.
- **Line breaks**: A line break ends a statement unless continuation is explicit.

### Line Break Rules

A line break is treated as **whitespace** (continuation) when it appears:

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

Line breaks immediately after scope-exiting keywords (`return`, `yield`, `raise`, `break`, `continue`) are always **delimiters**, not continuation.

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

Dead code after scope-exiting statements (`return`, `raise`, `break`, `continue`) is always a syntax error.

```typhon
return
2 # Syntax error
```
