# Typhon

Typhon is a Python-compatible language with modern syntax: brace-based blocks, static type checking, and expression-oriented features.

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

### Sample code

See more examples in [Typhon Tests](test/Execute/RunFileTest/).


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

Typhon keeps Python semantics where possible, but changes syntax and some safety rules.

### Main Changes

- **Brace Scoping**: Typhon uses `{ ... }` for blocks instead of indentation. Both `;` and line breaks can terminate statements. See [Lexical Structure](doc/reference/lexical_structure.md).
- **Static Typing**: Type checking is enforced at compile time. Currently powered by [basedpyright](https://docs.basedpyright.com/latest/) type checker.
- **Declarations**: Variables must be declared with `let` (immutable) or `var` (mutable). See [Variables](doc/reference/variables.md).

### Syntax Extensions

- **Null Safety**: `?.`, `??`, `?()`, `?[]` operators. See [Null Safety](doc/reference/expressions/null_safety.md).
- **Function literals**: Arrow functions such as `(x) => { return x + 1 }` have the same capability as regular functions. See [Function literals](doc/reference/expressions/literals.md#function-literals).
- **Pipe Operator**: `x |> f` for function chaining. See [Pipe Operator](doc/reference/expressions/pipe_operator.md).
- **Placeholders**: `_` for concise anonymous functions (e.g., `_ + 1`). See [Placeholders](doc/reference/expressions/placeholders.md).
- **Control Comprehensions**: Control forms as expressions (for example, `(if (c) x else y)`). `if/while/for/let/try/with/match` are supported. See [Comprehensions](doc/reference/expressions/comprehensions.md).
- **Pattern Matching**: Enhanced `match`, `if-let`, and `let-else` statements. See [Control Flow](doc/reference/statements/control_flow.md).
- **`self` Keyword**: In non-`static` methods, `self` is implicit and explicit `self` parameters are forbidden (including `__init__`). See [Classes](doc/reference/definitions/classes.md).
- **Data Records**: Anonymous immutable records such as `{|x = 1|}`. See [Types](doc/reference/types.md).
- **Block Comments**: `#( ... )#` allows nested comments.

### Detailed Design Changes

- **Logical Operators**: `&&`, `||`, `!` replace `and`, `or`, `not` (though Python keywords are still reserved).
- **Const Parameters**: Function parameters are immutable by default.
- **Header Parentheses Convention**: Forms that introduce a braced inner scope use parenthesized headers (for example, `with (...) { ... }`), while forms that declare into the current scope omit them (for example, inline `with let ...` and `let-else`).
- **Line Breaks**: Stricter rules for line continuations. See [Lexical Structure](doc/reference/lexical_structure.md).

### Syntax Restrictions

Some Python features are removed to enforce safety and clarity. See [Removed Features](doc/reference/removed_features.md).

- No `del`, `global`, `nonlocal`.
- No wildcard imports.
- No chained assignments (`a = b = c`).
- No control statements inside class bodies.

## Usage

Typhon can be run directly or translated to Python.

`.typh` files are Typhon source files. In directory mode, Typhon processes all `.typh` files.

Typhon uses a `.typhon` directory under source paths for translated Python and caches. At the same time, `.typhon-server` is used for language server temporal data.

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

Repository policy highlights:

- Use `uv run -m ...` as the default script execution style.
- Keep documentation concise, practical, and example-focused rather than long or decorative.
