# Typhon

Typhon is a overhaul syntax sugar for Python for modernization.

## Syntax Changes

Syntax in Python is supported unless it is explicitly changed or forbidden.

### Main changes

- Replacing offside rule by standard brace scope and semicolon delimiter. Line breaks also work as delimiter at the END of statement(there is formal rules below, in the clause "Detail design change").

- Type checking and compile time syntax/type error.

- Forced constant/variable declaration with strict lexical scope by `let` and `var` keywords. `let` is immutable and `var` is mutable.

- Unrestricted lambda function in the form of `(x) => {}`. With type annotation it have the form `(x: int) -> int => { return x + 1; }`. Abbreviation for single expr `(x) => x + 1` is also supported.

- `self` is keyword. First parameter of method definition is NOT self anymore. Use `static def` to prevent this feature.

### Syntax Extension

- Type annotations extension
  The place we can write type annotations is expanded beyond the limit of Python [PEP 526](https://peps.python.org/pep-0526/#specification).

- `(int, str)` for tuple type, `[int]` for list type. These must be used in unpack assignment annotation. Note this is valid only for typing context.

- Function Types
  Arrow types `(T1, T2) -> R` are syntax sugar for Protocol. Single argument can be written as `T -> R`. For example `(x1: T1, x2: T2) -> R` is translated into the following form.
  ```python
  class MyProtocol(Protocol):
      def __call__(self, x1: T1, x2: T2) -> R: ...
  ```

- Optional types `T?` equivalent to `T | None`.

- Nullable/Optional operators. Results to `None` when LHS `is None`.
  - `?.` for optional attribute access.
  - `??` for nullish coalescing.
  - `?()` for optional call.
  - `?[]` for optional subscript.

- `if-let` statement for checking optional/condition/matching.
  - `if (let x = f()) {...}` is same as `{ let x = f(); if (x is not None) {...} }`
  - `if (let x = f(); x > 0) {...}` is same as `{ let x = f(); if (x > 0) {...} }`
  - `if (let [1, 2, x, *y] = f(); x > 0) {...}` is same as `match (f()) { case([1, 2, x, *y]) if (x > 0) {...} }`

- `let-else` statement to flatten the `if-let` scope. In `else` block the code must exit by `return`, `raise`, `break`, `continue`.
  - `let Point(x=a, y=0) = point else { return None }` falls to the following code when match succeeded, `a` can be used there.

- Inline `with` statement.
  `with let f = open("file");` exits at the end of current scope. This is the same as with statement including the rest of current scope as its block.

- Const member of class
  `let x: T` in class is immutable member. Translated into `x: Final[T]`. Be attention not to use `Final` with `let` in Typhon code.

- Pipe operator
  `x |> f` is same as `f(x)`. This is left association with lowest priority.
  `x ?|> f` is optional pipe, is called when `x is not None`.

- Placeholder anonymous function (TODO)
  `_` in expression is placeholder for anonymous function. For example, `f(x, _, z)` is same as `(y) => f(x, y, z)`, `_ + _` is same as `(x, y) => x + y`.
  The expression strictly including `_` is converted to function. Note that single `_` alone is NOT the target. The expression bound to the placeholder is the one inside the innermost BOUNDARY determined by the following rules,
  - Arguments in function call are BOUNDARY. e.g. `f(_ + 1)` is `f((x) => x + 1)`, `f(g(_))` is `f((x) => g(x))` (here, `_` itself is NOT the target, so `g(_)` as `f`'s argument is the target).
  - Pipe operators's both operand are BOUNDARY. e.g. `v |> f(_)` is `v |> ((x)=>f(x))`.
  - Function literal's value is a BOUNDARY. e.g. `(x) => f(x, _)` is `(x) => ((y) => f(x, y))`

  If an expression has several placeholder `_` inside, it becomes multiple positional only parameter function, the parameter order from left to light. For example, `_ + _ * _` becomes `(x, y, z) => x + y * z`.

- Control statement comprehension expressions. `if/while/try/with/match` surrounded by paren, synonym to generator expression by `for`.
  - `(if (cond1) 1 elif (cond2) 2 else 3)`. `elif` and `else` is optional, the value is `None` for unspecified case.
  - `(while(cond) yield x)` is alternative generator expression. `while` can be used instead of `for`.
  - `(try x/y except(e: ZeroDivisionError) 0)`. `except` is optional. `(try x/y)` is `None` on exception.
  - `(with (let f = open("file.txt")) f.read())`.
  - `(match (f()) case(x, 0) x case(x, y) x + y)`. The default case is optional, results `None` on abbreviation.

- Data record literal `{|x = 1, y = "2"|}` which is translated into anonymous dataclass. The type is data record type `{|x: int, y: str|}` which is Protocol of dataclass. Attribute access `val.x` , unpacking by `{|x, y|}` or patten matching by specific pattern `{|x = a, y = b|}` is supported. (TODO)

### Detail design changes

- Logical operators
  `and`, `or`, `not` operators are replaced by `&&`,`||`, `!`, though they are still reserved as keyword (Note `in`, `not in`, `is`, `is not` are still supported).

- Assignment style in with and except statement
  Apply normal assignment or declaration syntax to with and except. e.g. `with (let f = open(...)) {}`, `except (e: IOError) {}`

- Static Temporal Dead Zone(TDZ) is introduced in module top-level for recursive definition.
  - Reference to symbol declared after is allowed in function (`def` and function literal). Such function symbol is marked as DEAD until all the declaration is completed.
  - Reference to DEAD symbol in function is also allowed. The DEAD mark is propagated.
  - Otherwise reference to symbol is error if that is DEAD or not declared yet.

- Parameters are const, you can shadow it using `let/var`.

- Builtin symbols are all const, you can shadow it using `let/var`.

- Comprehension uses `yield` keyword to determine the expression part.
  For example, `[for (let i in range(1, 10)) if (i % 2 == 1) yield i * i]`, that is translated into `[i * i for i in range(1, 10) if i % 2 == 1]`.
  For dict, `let odd_square = {for (let i in range(1, 10)) if (i % 2 == 1) yield i: i * i}`

- Line breaks are regarded as delimiter. But when the statement looks like to continue in newline, line breaks only work as whitespace.
  The line break is only a whitespace at the position matching any of the following rules.
  - Just after,
    - all operators (including `,`, `.`, `=`, `?`, `:`, `=>`, `->`).
    - brackets open `([{`.
    - modifiers(`static`, `async`) and decorators.
    - all keyword of statements, EXCEPT for return/break like ones (`return`, `raise`, `yield`, `break`, `continue`).
    - closing paren `)` of the following paren of statement keywords (`class`, `def`, `if`, `elif`, `while`, `for`, `except`, `with`, `match`, `case`). For example last `)` of `if (cond)` or `class[T](B)`.

  - Just before,
    - all operators. EXCEPT for `@`, `await`
    - brackets close `}])`.
    - keyword of statement that appears in the middle (`elif`, `else`, `except`, `finally`, `case`)

### Syntax Restrictions

- Identifiers with prefix `_typh_` are all reserved.

- `del`, `global`, `nonlocal` are forbidden.

- Wildcard import `from m import *` is forbidden.

- Control statements inside class definition are forbidden. Only `class`, `def`, `let/var`, `import` are allowed. `let/var` declaration of multiple variable or unpacking is also forbidden.

- Chained assignments such as `a = b = 0` are forbidden.

- `,` separated assignment target and `,` separated tuple without paren around are forbidden. And even not parsed in such a way. `a, b = b, a` is invalid, use `(a, b) = (b, a)` instead.

- Dead code just after `return`/`raise` statement is forbidden.

- Original if expressions, the form `x if x > 0 else y` is forbidden.

- Lambda expression by 'lambda' is forbidden.

- Note all the forbidden keywords are still reserved.

## Bundled Libraries

TBD

- `typhon.traceback` is drop in replacement for builtin `traceback` to provide traceback display in Typhon's syntax.


## Influenced by

- Python
- Typescript
- Swift
- Rust
- Scala
- F#
- C#
