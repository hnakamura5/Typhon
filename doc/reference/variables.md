# Variables

Typhon enforces strict variable declaration and lexical scoping.

## Declarations

Variables must be declared with `let` or `var`. The left-hand side is a **pattern**, not only a name, so destructuring and matching are supported at declaration.

### Immutable Variables (`let`)

`let` declares an immutable binding. It cannot be reassigned.

```typhon
let x = 10
# x = 20; # Error: Cannot assign to immutable variable
```

### Mutable Variables (`var`)

`var` declares a mutable variable.

```typhon
var y = 10
y = 20 # OK
```

## Pattern Matching in Declarations

Because `let` and `var` accept patterns, you can destructure values directly. For all supported patterns, see [Patterns](statements/patterns.md).

### Irrefutable Patterns

Patterns that always match (like variable names or tuples of variable names) are called **irrefutable patterns**. These can be used directly in `let` and `var` declarations.

```typhon
let (a, b) = (1, 2)
let {.x, .y} = {|x = 10, y = 20|}
```

### Refutable Patterns and `let-else`

Patterns that may fail to match (for example, literals or specific variants) are **refutable patterns**. When using a refutable pattern in a declaration, you must provide an `else` block.

`let-else` binds names into the current scope, so this form does not use header parentheses.

The `else` block **must diverge** (`return`, `raise`, `continue`, or `break`), so the remaining scope cannot run with uninitialized bindings.

```typhon
let (1, x) = (1, 100) else {
    print("Pattern mismatch!")
    return
}
# x is bound to 100 here

let [head, *tail] = [] else {
    print("List is empty")
    return
}
```

If you try to use a refutable pattern without `else`, it is a compile-time error.

## Type Annotations in Patterns

Type annotations can be used in capture patterns in `for`, `with`, and `case`.

```typhon
for (let x: int in range(10)) { ... }
with (let f: TextIO = open("file.txt")) { ... }
match (v) {
    case (x: int, y: int) { ... }
}
```

Note: In `match`, annotations apply to bound variables and do not change runtime matching behavior.

## Built-in Symbols

Python built-ins are available as global **immutable** symbols.

```typhon
print(1)
```

```typhon
print = 1 # Error: Cannot assign to immutable symbol
```

## Scoping Rules

Typhon uses lexical block scope. Variables declared inside `{ ... }` are not visible outside the block.

```typhon
if (True) {
    let x = 100
}

# print(x) # Error: Undefined symbol
```

### Shadowing

Variables can be shadowed in inner scopes.

```typhon
let x = 1
if (True) {
    let x = 2 # Shadows outer x
    print(x) # Prints 2
}
print(x) # Prints 1
```

### Temporal Dead Zone (TDZ)

In general, variables must be declared before use. There is **no** temporal dead zone in local scopes: referencing a name before declaration is an error.

```typhon
# Error: x is not declared yet
print(x)
let x = 10
```

#### Module Top-Level: Static TDZ for Recursion

The **only** TDZ-like mechanism is at module top level, to support mutual recursion between function definitions.

At module top level, functions may reference symbols declared later. Such functions are temporarily marked as **DEAD** until all referenced symbols are defined. This is a compile-time mechanism.

**Rules:**

1. **Functions can reference forward-declared symbols**: A function at module top-level can call another function defined later.

   ```typhon
   def foo() -> int {
       return bar() # bar not yet defined - foo becomes DEAD
   }

   def bar() -> int {
       return 42
   }
   # Now foo is no longer DEAD
   ```

2. **DEAD propagates**: If function `A` references DEAD function `B`, `A` also becomes DEAD.

   ```typhon
   def a() { return b() } # DEAD (b is DEAD)
   def b() { return c() } # DEAD (c not defined)
   def c() { return 1 }   # Not DEAD
   ```

3. **DEAD symbols cannot be called at top-level**: You cannot call a DEAD function in top-level executable code.

   ```typhon
   let x = foo() # Error: foo is DEAD

   def foo() -> int {
       return 42
   }
   ```

This mechanism allows module-level mutual recursion while preventing premature execution.

**Important**: This behavior applies **only** at module top level. In all other scopes, declarations must appear before use.
