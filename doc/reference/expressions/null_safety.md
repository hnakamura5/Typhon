# Null Safety

Typhon provides operators to safely handle `None` (optional) values.

## Optional Chaining (`?.`)

Access attributes or methods only if the receiver is not `None`.

```typhon
let x: Foo? = get_foo()
let y = x?.bar # y is None if x is None, else x.bar
```

## Nullish Coalescing (`??`)

Provide a default value if the left-hand side is `None`.

```typhon
let x: int? = None
let y = x ?? 0 # y is 0
```

## Optional Call (`?()`)

Call a function only if it is not `None`.

```typhon
let f: ((int) -> int)? = None
f?(10) # Returns None, does not crash
```

## Optional Subscript (`?[]`)

Access an index/key only if the collection is not `None`.

```typhon
let l: [int]? = None
let val = l?[0]
```

## Optional Pipe (`?|>`)

The optional pipe operator. See [Pipe Operator](pipe_operator.md)
