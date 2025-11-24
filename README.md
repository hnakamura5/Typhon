# Typhon

Typhon is a modernized syntax sugar for Python, designed to improve developer experience with features like static typing, brace-based scoping, and expressive functional programming capabilities.

## Design Concepts

Typhon is built on three core pillars:

1. **Safety**: As expected from modern programming languages, Typhon enforces safety through static typing, lexical scopes, immutable-by-default variables (`let`), and null safety features (`?.`, `??`).
2. **Expressiveness**: Expression-oriented design with functional programming features. Control comprehension forms for `if`, `match`, `try`, and so on enable concise, value-returning expressions. Function literals, placeholders and pipe operators facilitate clean and readable code.
3. **Python Interoperability**: Typhon compiles directly to Python, allowing you to use the vast ecosystem of Python libraries seamlessly while enjoying a modern syntax.

## Documentation

For a complete guide to the language, please visit the **[Typhon Reference Manual](doc/reference/README.md)**.

### Quick Links

- [Lexical Structure](doc/reference/lexical_structure.md) (Comments, Keywords, Delimiters)
- [Types](doc/reference/types.md)
- [Variables](doc/reference/variables.md)
- [Expressions](doc/reference/expressions/README.md)
- [Statements](doc/reference/statements/README.md)
- [Definitions](doc/reference/definitions/README.md) (Functions, Classes, Modules)
- [Removed Features](doc/reference/removed_features.md)

## Syntax Changes from Python

Typhon retains most of Python's semantics but introduces significant syntax changes.

### Main Changes

- **Brace Scoping**: Typhon uses `{ ... }` for blocks, replacing indentation-based scoping. Both `;` and line breaks can also act as delimiters. See [Lexical Structure](doc/reference/lexical_structure.md).
- **Static Typing**: Type checking is enforced at compile time.
- **Declarations**: Variables must be declared with `let` (immutable) or `var` (mutable). See [Variables](doc/reference/variables.md).

### Syntax Extensions

- **Null Safety**: `?.`, `??`, `?()`, `?[]` operators. See [Null Safety](doc/reference/expressions/null_safety.md).
- **Function literals**: Unrestricted function literals with `(x) => { return x + 1 }` syntax, with totally the same capability as normal functions. See [Functions](doc/reference/items/functions.md).
- **Pipe Operator**: `x |> f` for function chaining. See [Pipe Operator](doc/reference/expressions/pipe_operator.md).
- **Placeholders**: `_` for concise anonymous functions (e.g., `_ + 1`). See [Placeholders](doc/reference/expressions/placeholders.md).
- **Control Comprehensions**: Control statements as expressions (e.g., `(if (c) x else y)`). All `if/while/for/let/try/with/match` are supported as comprehension. See [Comprehensions](doc/reference/expressions/comprehensions.md).
- **Pattern Matching**: Enhanced `match`, `if-let`, and `let-else` statements. See [Control Flow](doc/reference/statements/control_flow.md).
- **`self` Keyword**: `self` is a keyword and is not explicitly declared in method signatures. See [Classes](doc/reference/items/classes.md).
- **Data Records**: Anonymous immutable structs `{|x=1|}`. See [Types](doc/reference/types.md).
- **Block Comments**: `#( ... )#` allows nested comments.

### Detailed Design Changes

- **Logical Operators**: `&&`, `||`, `!` replace `and`, `or`, `not` (though Python keywords are still reserved).
- **Const Parameters**: Function parameters are immutable by default.
- **Line Breaks**: Stricter rules for line continuations. See [Lexical Structure](doc/reference/lexical_structure.md).

### Syntax Restrictions

Some Python features are removed to enforce safety and clarity. See [Removed Features](doc/reference/removed_features.md).

- No `del`, `global`, `nonlocal`.
- No wildcard imports.
- No chained assignments (`a = b = c`).
- No control statements inside class bodies.

## Usage

Typhon can be run directly or translated to Python.

### Run

Run a Typhon source file or directory.

```bash
typhon run <source> [args...]
```

### Translate

Translate Typhon code to Python.

```bash
typhon translate <source> [-o output_dir]
```

### Type Check

Run type checking on Typhon code.

```bash
typhon type_check <source>
```

## Future Plans

See [Future Plans](doc/reference/future_plans.md) for planned features like compile-time controls (`static if`) and known limitations.

## Influenced By

Typhon draws inspiration from several modern programming languages:

- **Python**: The foundation of Typhon's semantics and ecosystem.
- **TypeScript**: Static typing on top of a dynamic language, structural typing concepts.
- **Swift**: Optional chaining, `if-let` syntax, and clean closure syntax.
- **Rust**: Expression-oriented syntax, `match` statement power, and immutable-by-default philosophy.
- **Scala**: Functional programming features and concise syntax.
- **F#**: Pipe operators and type inference concepts.
- **C#**: Modern language features and tooling.
