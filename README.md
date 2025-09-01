# Typhon

Typhon is a syntax sugar for Python with small modifications for modernization.

## Syntax Changes

### Main changes

- Replacing offside rule by standard brace scope and semicolon delimiter.

- Type checking and compile time syntax/type error.

- Forced variable/constant declaration and scoping by `var` and `let`

- Unrestricted lambda function in the form of `(x)=>{}`. With type annotation it have the form `(x:int)->int => { return x + 1; }`.

- Nullable/Optional chain operators `??`, `?.`, `?:` and so on.

- `self` is keyword. First parameter of method definition is NOT self anymore. Use `static def` to prevent this feature.

### Syntax Extension

- Type annotations extension
  The place we can write type annotations is expanded beyond the limit of Python [PEP 526](https://peps.python.org/pep-0526/#specification). TODO

- Function Types
  Arrow types `(T1, T2) -> R` are syntax sugar for Protocol. For example `(x1: T1, x2: T2) -> R` is translated into the following form.
  ```python
  class MyProtocol(Protocol):
      def __call__(self, x1: T1, x2: T2) -> R: ...
  ```

- Scoped `with` statement.
  `with let f = open("file");` exits at the end of current scope. This is the same as with statement including the rest of current scope as its block.

- `if-let` statement for checking optional/condition
  `if (let x = f()){...}` is same as `{let x = f(); if (x is not None){...}}`
  `if (let x = f(); x > 0){...}` is same as `{let x = f(); if (x > 0){...}}`

- `while-let` statement for checking optional/condition
  `while (let x = f()) {...}` behaves as `{let x = f(); while(x is not None){...}`
  `while (let x = f(); x > 0) {...}` behaves as `{let x = f(); while(x > 0)}{...}`

- Const member of class
  `let x:int` in class is immutable member. Translated into `@property`.

### Detail design changes

- Logical operators
  `and`, `or`, `not` operators are replaced by `&&`,`||`, `!`, though they are still reserved as keyword (Note `in`, `not in`, `is`, `is not` are supported).

- Assignment style in with and except statement
  Apply normal assignment or declaration syntax to with and except. e.g. `with(let f=open(...)) {}`, `except(e: IOError){}`

- Static Temporal Dead Zone(TDZ) is introduced in module top-level for recursive definition.
  - Reference to symbol declared after is allowed in function (`def` and function literal). Such function symbol is marked as DEAD until all the declaration is completed.
  - Reference to DEAD symbol in function is also allowed. The DEAD mark is propagated.
  - Otherwise reference to symbol is error if that is DEAD or not declared yet.

- Parameters are const, you can shadow it using `var/let`.

- Builtin symbols are all const, you can shadow it using `var/let`.

### Syntax Restrictions

- Identifiers with prefix `_typh_` are all reserved.
- `del`, `global`, `nonlocal` are forbidden.
- Wildcard import `from m import *` is  forbidden.
- Control statements inside class definition are forbidden. Only `class`, `def`, `var/let`, `import` are allowed.

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

