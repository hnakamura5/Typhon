# Typhon

Typhon is a modernized syntax sugar for Python, designed to improve developer experience with features like static typing, brace-based scoping, and expressive functional programming capabilities.

- GitHub repository: [Typhon](https://github.com/hnakamura5/Typhon)
- PyPI package: [Typhon-Language](https://pypi.org/project/Typhon-Language/)
- VSCode extension: [Typhon Language Support](https://marketplace.visualstudio.com/items?itemName=hnakamura5.typhon-language-support) from [GitHub Repository](https://github.com/hnakamura5/typhon-language-support)

## Getting Started

Install Typhon via pip:

```bash
pip install typhon-language
```

Run Typhon from the command line:

```bash
typhon --help
```

Create a simple Typhon program in `hello.typh`:

```typhon
def main() {
    print("Hello, Typhon!")
}
main()
```

Run the program:

```bash
typhon run hello.typh
```

Or run directly using uvx:

```bash
uvx --from typhon-language typhon run hello.typh
```

## Design Concepts

Typhon is built on three core pillars:

1. **Safety**: As expected in modern programming languages, Typhon enforces safety through static typing, lexical scopes, immutable-by-default variables (`let`), and null safety features (`?.`, `??`, `?()`, `?[]`).
2. **Expressiveness**: Expression-oriented design with functional programming features. Control comprehension forms for `if`, `match`, `try`, and so on enable concise, value-returning expressions. Function literals, placeholders and pipe operators facilitate clean and readable code.
3. **Python Interoperability**: Typhon compiles directly to Python, allowing you to use the vast ecosystem of Python libraries seamlessly while enjoying a modern syntax.

### How it looks like

You can see small code snippets in the test directory: [Typhon Tests](test/execute/RunFileTest/).


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

- **Brace Scoping**: Typhon uses `{ ... }` for blocks, replacing indentation-based scoping. Both `;` and line breaks can also act as delimiters. See [Lexical Structure](doc/reference/lexical_structure.md) for more details.
- **Static Typing**: Type checking is enforced at compile time. Currently powered by [basedpyright](https://docs.basedpyright.com/latest/) type checker.
- **Declarations**: Variables must be declared with `let` (immutable) or `var` (mutable). See [Variables](doc/reference/variables.md).

### Syntax Extensions

- **Null Safety**: `?.`, `??`, `?()`, `?[]` operators. See [Null Safety](doc/reference/expressions/null_safety.md).
- **Function literals**: Unrestricted function literals with `(x) => { return x + 1 }` syntax, with totally the same capability as normal functions. See[Function literals](doc/reference/expressions/literals.md#function-literals).
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

`.typh` files are Typhon source files. In directory mode, all `.typh` files are processed.

Note Typhon uses `.typhon` directory in source paths to place translated Python files and caches.

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

- Python
- TypeScript
- Swift
- Rust
- Scala
- F#

## Agent Configuration (Copilot / Claude Code)

This repository contains shared agent configuration files:

- [AGENTS.md](AGENTS.md): repository rules and policies.
- [SKILLS.md](SKILLS.md): minimal operational workflow and script usage.

Tool-specific entry files refers the shared files:

- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [CLAUDE.md](CLAUDE.md)
