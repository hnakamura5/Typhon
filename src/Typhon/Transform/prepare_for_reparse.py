import ast

from ..Grammar.typhon_ast import is_reparse_target
from ._utils.imports import (
    add_import_for_runtime_checkable,
    add_import_for_dataclass,
    add_import_for_final,
    add_import_for_protocol,
)


def prepare_for_reparse(module: ast.Module) -> None:
    if not is_reparse_target(module):
        return
    # Prepare builtin imports to stabilize the re-parse result.
    # By removing the effect of imports in the reparsed part.
    add_import_for_final(module)
    add_import_for_dataclass(module)
    add_import_for_protocol(module)
    add_import_for_runtime_checkable(module)
