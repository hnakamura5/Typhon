# Control Comprehensions

Typhon treats control-flow forms as expressions when wrapped in parentheses.

## If Comprehension

```typhon
let x = (if (cond1) 1 elif (cond2) 2 else 3)
```

If `else` is omitted and the condition is false, the result is `None`.

## Match Comprehension

```typhon
let res = (match (val) case (1) "one" case (x, y) x + y)
```

The default case is optional (result is `None` if no case matches).

## Try Comprehension

```typhon
let val = (try x / y except (ZeroDivisionError) 0)
```

Returns `None` if an exception occurs and is not handled in the expression.

`try` comprehension supports the same clauses as statement `try`, except `else` is not allowed.

## Let Comprehension

```typhon
let y = (let x = 1; x + 1)
```

The declaration and expression are separated by `;`. The last expression is the value. `var` is not allowed in block expressions.

## With Comprehension

```typhon
let content = (with (let f = open("file.txt")) f.read())
```

## Generator Comprehensions

Python-style comprehensions are supported, but Typhon uses `yield` explicitly for produced values.

```typhon
[for (i in range(10)) if (i % 2 == 0) yield i * i]
```

Typhon also allows using `while` in comprehensions.

```typhon
(while (cond) yield x)
```

List/dict/set/generator comprehension forms are supported.

`for` and `while` comprehensions follow statement forms, except `else` is not allowed.
