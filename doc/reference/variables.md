# Variables

Typhon enforces strict variable declaration and lexical scoping.

## Declarations

Variables must be declared using `let` or `var`.

### Immutable Variables (`let`)

`let` declares an immutable binding. The value cannot be reassigned.

```typhon
let x = 10;
# x = 20; # Error: Cannot assign to immutable variable
```

### Mutable Variables (`var`)

`var` declares a mutable variable.

```typhon
var y = 10;
y = 20; # OK
```

## Type Annotations in Patterns

Type annotations can be used in `for`, `with`, and `case` capture patterns.

```typhon
for (let x: int in range(10)) { ... }
with (let f: TextIO = open("file.txt")) { ... }
match (v) {
    case (x: int, y: int) { ... }
}
```

Note: In `match`, the annotation applies to the *result* of the match (the bound variable), it does not affect the matching logic itself (runtime check).

## Scoping Rules

Typhon uses standard block scope (lexical scope). Variables declared inside a block `{ ... }` are not visible outside of it.

```typhon
if (True) {
    let local = 100;
}

# print(local); # Error: Undefined symbol
```

### Shadowing

Variables can be shadowed in inner scopes.

```typhon
let x = 1;
if (True) {
    let x = 2; # Shadows outer x
    print(x); # Prints 2
}
print(x); # Prints 1
```

### Temporal Dead Zone (TDZ)

In general, variables in Typhon must be declared before they are accessed. There is **no** temporal dead zone in local scopes - you simply cannot reference a variable before it's declared.

```typhon
# Error: x is not declared yet
print(x);
let x = 10;
```

#### Module Top-Level: Static TDZ for Recursion

The **only** place where Typhon has a Temporal Dead Zone mechanism is at module top-level, to support mutual recursion between function definitions.

At module top-level, functions can reference symbols that are declared later in the module. Such functions are temporarily marked as **DEAD** until all the symbols they reference are defined. This DEAD marking is purely a compile-time mechanism.

**Rules:**

1. **Functions can reference forward-declared symbols**: A function at module top-level can call another function defined later.

   ```typhon
   def foo() -> int {
       return bar(); # bar not yet defined - foo becomes DEAD
   }

   def bar() -> int {
       return 42;
   }
   # Now foo is no longer DEAD
   ```

2. **DEAD propagates**: If function A references DEAD function B, then A also becomes DEAD.

   ```typhon
   def a() { return b(); } # DEAD (b is DEAD)
   def b() { return c(); } # DEAD (c not defined)
   def c() { return 1; }   # Not DEAD
   ```

3. **DEAD symbols cannot be called at top-level**: You cannot call a DEAD function in top-level executable code.

   ```typhon
   let x = foo(); # Error: foo is DEAD

   def foo() -> int {
       return 42;
   }
   ```

This mechanism enables mutual recursion at module level while preventing premature execution of functions that depend on not-yet-defined symbols.

**Important**: This TDZ mechanism applies **only** to module top-level. In all other scopes (functions, blocks, etc.), variables must simply be declared before use - there is no special handling.
