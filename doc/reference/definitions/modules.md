# Modules

## Imports

Typhon supports standard Python imports, but wildcard imports `from m import *` are forbidden.

```typhon
import math;
from os import path;
```

## Program Structure

A Typhon program consists of modules.

## Temporal Dead Zone (TDZ)

Module-level recursion is supported, but symbols must be defined before use (except inside functions where they can be "DEAD" until definition).
