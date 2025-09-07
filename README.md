# Typhon

Typhon is a syntax sugar for Python with small modifications for modernization.

## Syntax Changes

### Main changes

- Replacing offside rule by standard brace scope and semicolon delimiter.

- Type checking and compile time syntax/type error.

- Forced constant/variable declaration with strict lexical scope by `let` and `var` keywords. `let` is immutable and `var` is mutable.

- Unrestricted lambda function in the form of `(x) => {}`. With type annotation it have the form `(x: int) -> int => { return x + 1; }`. Abbreviation for single expr `(x) => x + 1` is also supported.

- `self` is keyword. First parameter of method definition is NOT self anymore. Use `static def` to prevent this feature.

### Syntax Extension

- Type annotations extension
  The place we can write type annotations is expanded beyond the limit of Python [PEP 526](https://peps.python.org/pep-0526/#specification).

- `(int, str)` for tuple type, `[int]` for list type. These must be used in unpack assignment annotation. (TODO)

- Function Types
  Arrow types `(T1, T2) -> R` are syntax sugar for Protocol. For example `(x1: T1, x2: T2) -> R` is translated into the following form.
  ```python
  class MyProtocol(Protocol):
      def __call__(self, x1: T1, x2: T2) -> R: ...
  ```

- Nullable/Optional chain operators `??`, `?.`, `?:` and so on. (TODO)

- `if-let` statement for checking optional/condition/matching. (TODO)
  - `if (let x = f()) {...}` is same as `{ let x = f(); if (x is not None) {...} }`
  - `if (let x = f(); x > 0) {...}` is same as `{ let x = f(); if (x > 0) {...} }`
  - `if (let [1, 2, x, *y] = f(); x > 0) {...}` is same as `match (f()) { case([1, 2, x, *y]) if (x > 0) {...} }`

- Scoped `with` statement. (TODO)
  `with let f = open("file");` exits at the end of current scope. This is the same as with statement including the rest of current scope as its block.

- Const member of class (TODO)
  `let x: int` in class is immutable member. Translated into `@property`.

### Detail design changes

- Logical operators (TODO)
  `and`, `or`, `not` operators are replaced by `&&`,`||`, `!`, though they are still reserved as keyword (Note `in`, `not in`, `is`, `is not` are still supported).

- Assignment style in with and except statement
  Apply normal assignment or declaration syntax to with and except. e.g. `with (let f = open(...)) {}`, `except (e: IOError) {}`

- Static Temporal Dead Zone(TDZ) is introduced in module top-level for recursive definition.
  - Reference to symbol declared after is allowed in function (`def` and function literal). Such function symbol is marked as DEAD until all the declaration is completed.
  - Reference to DEAD symbol in function is also allowed. The DEAD mark is propagated.
  - Otherwise reference to symbol is error if that is DEAD or not declared yet.

- Parameters are const, you can shadow it using `let/var`.

- Builtin symbols are all const, you can shadow it using `let/var`.

- Comprehension uses yield keyword to determine the expression part.
  For example, `[for (let i in range(1, 10)) if (i % 2 == 1) yield i * i]`, that is translated into `[i * i for i in range(1, 10) if i % 2 == 1]`.
  For dict, `let odd_square = {for (let i in range(1, 10)) if (i % 2 == 1) yield i: i * i}`


### Syntax Restrictions

- Identifiers with prefix `_typh_` are all reserved.

- `del`, `global`, `nonlocal` are forbidden.

- Wildcard import `from m import *` is forbidden.

- Control statements inside class definition are forbidden. Only `class`, `def`, `let/var`, `import` are allowed.

- Chained assignments such as `a = b = 0` are forbidden.

- `,` separated assignment target and `,` separated tuple without paren around are forbidden. And even not parsed in such a way. `a, b = b, a` is invalid, use `(a, b) = (b, a)` instead.

## Bundled Libraries

TBD

- `typhon.chain` is a library that provides a fluent interface for working with iterables.
  - `chain` is a function that allows chaining operations on collections, similar to `map`, `filter`, and `reduce`.
  ```typhon
  from typhon.chain import chain
  let result = chain([1, 2, 3])
      .map((x) => x + 1)
      .filter((x) => x > 2);
  ```

- `typhon.traceback` is drop in replacement for builtin `traceback` to provide traceback display in Typhon's syntax.

