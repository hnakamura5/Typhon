# Classes

## Class Definition

Classes are defined using `class`.

```typhon
class Point {
    let x: int;
    let y: int;

    def __init__(self, x: int, y: int) {
        self.x = x;
        self.y = y;
    }
}
```

## Self

`self` is a keyword in Typhon. It is NOT passed as the first argument in the method definition signature, but it is available in the body.

```typhon
class C {
    def method() {
        print(self);
    }
}
```

## Static Methods

Use `static def` for static methods (no `self`).

```typhon
class C {
    static def create() {
        return C();
    }
}
```

## Const Members

`let` members in a class are immutable. They are translated to `Final[T]` in Python.

```typhon
class C {
    let x: int = 10;
    # x = 20; # Error: Cannot assign to immutable member
}
```

Note: Do not use `Final` with `let` manually, as `let` implies it.
