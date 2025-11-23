# Context Management

## With Statement

Manage resources using `with`.

```typhon
with (let f = open("file.txt")) {
    f.read();
}
```

## Inline With

Typhon supports an inline `with` statement that applies to the rest of the current scope.

if (True) {
    with let f = open("file.txt");
    f.read();
} # f is closed here
```
