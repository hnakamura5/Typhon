# Control Comprehensions

Typhon treats control flow statements as expressions when wrapped in parentheses.

## If Comprehension

```typhon
let x = (if (cond1) 1 elif (cond2) 2 else 3);
```

If `else` is omitted and the condition is false, the result is `None`.

## Match Comprehension

```typhon
let res = (match (val) case (1) "one" case (x, y) x + y);
```

Default case is optional (result is `None` if no match).

## Try Comprehension

```typhon
let val = (try x / y except (ZeroDivisionError) 0);
```

Returns `None` if an exception occurs and is not caught by the expression's handler (or if the handler doesn't return a value? *Clarification needed: README says "(try x/y)" is None on exception. It implies simple try-except block behavior*).

## Let Comprehension

```typhon
let y = (let x = 1; x + 1);
```

Declaration and the expression are separated by `;`. The last expression is the value. `var` is not allowed in block expressions.

## With Comprehension

```typhon
let content = (with (let f = open("file.txt")) f.read());
```

## Generator Comprehensions

Standard Python comprehensions are supported, but `yield` keyword is used to be explicit about the yielded value.

```typhon
[for (i in range(10)) if (i % 2 == 0) yield i * i]
```

Typhon also allows using `while` in comprehensions.

```typhon
(while (cond) yield x)
```

All the list/dict/set/generator comprehension forms from Python are supported.
