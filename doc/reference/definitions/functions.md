# Functions

## Function Definition

Functions are defined with `def`.

```typhon
def add(x: int, y: int) -> int {
    return x + y
}
```

## Static Functions

Functions can be marked `static` (for example, in classes).

```typhon
class Math {
    static def add(x, y) { return x + y }
}
```

## Async Functions

Async functions use `async def`.

```typhon
async def fetch_data() { ... }
```

## Arrow Functions

Typhon supports arrow functions for concise anonymous functions.

```typhon
let add = (x, y) => x + y
let typed_add = (x: int, y: int) -> int => x + y
```

## Parameters

- **Positional-only**: `/`
- **Keyword-only**: `*`
- **Varargs**: `*args`
- **Kwargs**: `**kwargs`

Parameters are immutable by default. Shadow them if mutation is needed.

```typhon
def f(x) {
    # x = 1 # Error
    let x = 1 # OK (shadowing)
}
```
