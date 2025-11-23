# Assignment

## Simple Assignment

Assignment binds a value to a variable. In Typhon, variables must be declared with `let` or `var` before assignment, or assigned at declaration.

```typhon
var x = 1;
x = 2;
```

## Augmented Assignment

Typhon supports standard augmented assignments.

```typhon
var x = 1;
x += 1;
```

## Destructuring Assignment

Typhon supports destructuring for tuples and lists.

```typhon
let (a, b) = (1, 2);
let [x, *y] = [1, 2, 3];
```

Note: Chained assignments `a = b = c` are forbidden.
