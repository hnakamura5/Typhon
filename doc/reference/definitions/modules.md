# Modules

## Program Structure

A Typhon program consists of modules.

Each directory can be a module constructed with all `.typh` files in it, plus an optional `__init__.typh` file.
Even if `__init__.typh` is not present, the directory is always treated as a module.

`__main__.typh` is the entry point module when running as a Typhon program.

## Imports

Typhon supports standard Python imports, but wildcard imports `from m import *` are forbidden.

```typhon
import math;
from os import path;
```

## Static Temporal Dead Zone (TDZ)

Module-level recursion is supported, but symbols must be defined before use (except inside functions where they can be "DEAD" until definition).
Refer to [Variables](../variables.md#module-top-level-static-tdz-for-recursion) for details.
