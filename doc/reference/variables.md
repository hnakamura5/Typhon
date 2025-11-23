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
Variables cannot be accessed before their declaration. This includes module-level recursion where a symbol is marked as "DEAD" until fully defined.
