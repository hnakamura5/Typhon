# Typhon

Typhon is a syntax sugar for Python with small modifications for modernization.

- Replacing offside rule by standard brace scope and semicolon delimiter.
- Type checking and compile time error.
- Optional chain operators `??`, `?.` and so on.
- Constant binding. TODO
- `self` is keyword. First parameter of method definition is NOT self anymore.

Also, small design changes are included.

- Logical operators
  `and`, `or`, `not` operators are replaced by `&&`,`||`, `!`, though they are still reserved as keyword (Note `in`, `not in`, `is`, `is not` are supported).

- Type annotations
  The place we can write type annotations is expanded beyond the limit of Python [PEP 526](https://peps.python.org/pep-0526/#specification). TODO

