# Typhon

Typhon is a syntax sugar for Python with small modifications for modernization.

## Syntax Changes

- Replacing offside rule by standard brace scope and semicolon delimiter.
- Type checking and compile time error.
- Forced variable/constant declaration and scoping by `let` and `const`
- Nullable/Optional chain operators `??`, `?.`, `?:` and so on.
- `self` is keyword. First parameter of method definition is NOT self anymore.
- Unrestricted lambda function in the form of `(x)=>{}`

Also, small design changes are included.

- Logical operators
  `and`, `or`, `not` operators are replaced by `&&`,`||`, `!`, though they are still reserved as keyword (Note `in`, `not in`, `is`, `is not` are supported).

- Type annotations
  The place we can write type annotations is expanded beyond the limit of Python [PEP 526](https://peps.python.org/pep-0526/#specification). TODO

- Function Types
  `(T1, T2)->R` is syntax sugar of `Callable[[T1, T2], R]`.
  such as `(x1: T1, x2: T2) -> R` is syntax sugar of `Protocol` subtype.
  ```python
  class MyProtocol(Protocol):
      def __call__(self, x1: T1, x2: T2) -> R: ...
  ```

- Assignment in with and except statement
  Apply normal assignment or declaration syntax to with and except. e.g. `with(const f=open(...)) {}`, `except(e: IOError){}`

## Restriction

- Identifier with prefix `_typh_` is all reserved.

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


