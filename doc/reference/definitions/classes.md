# Classes

## Class Definition

Classes are defined with `class`.

```typhon
class Point {
    let x: int
    let y: int

    def __init__(x: int, y: int) {
        self.x = x
        self.y = y
    }
}
```

## Self

`self` is a Typhon keyword. In non-`static` methods (including `__init__`), explicitly writing `self` in parameter lists is forbidden. `self` is injected automatically and available in the body.

```typhon
class C {
    def method() {
        print(self)
    }
}
```

## Static Methods

Use `static def` for static methods (no `self`).

```typhon
class C {
    static def create() {
        return C()
    }
}
```

## Const Members

`let` members are immutable and translated to `Final[T]` in Python.

```typhon
class C {
    let x: int = 10
    # x = 20; # Error: Cannot assign to immutable member
}
```

Note: Do not use `Final` with `let` manually, as `let` implies it.
