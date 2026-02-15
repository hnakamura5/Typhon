# Modules

## Program Structure

A Typhon program consists of modules.

Each directory is treated as a package/module boundary containing all `.typh` files in that directory.

Semantically, Typhon treats every directory as if `__init__.py` exists.

`__init__.typh` is optional on the Typhon source side.

`__main__.typh` is the entry point module when running as a Typhon program.

## Imports

Typhon supports standard Python import forms, but forbids wildcard imports (`from m import *`).

```typhon
import math
from os import path
```

## Static Temporal Dead Zone (TDZ)

Module-level recursion is supported, but top-level execution cannot use symbols that are still marked `DEAD`.
Refer to [Variables](../variables.md#module-top-level-static-tdz-for-recursion) for details.
