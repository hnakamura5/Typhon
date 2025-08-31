import ast
from typing import Union, Any


typhon_prefix = "_typh_"

PythonScope = Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]


def get_protocol_name() -> str:
    return f"{typhon_prefix}_Protocol"


class UniqueNameGenerator:
    scope_id_counter: int
    scope_stack: list[tuple[PythonScope, str]] = []
    scope_counters: dict[str, int]

    def __init__(self):
        self.scope_id_counter = 0
        self.scope_counters = {}

    # Here the scope is Python scope: module, class, function. Not block scope.
    def enter_scope(self, scope: PythonScope):
        scope_id = f"{self._scope_symbol(scope)}{self.scope_id_counter}"
        self.scope_id_counter += 1
        self.scope_counters[scope_id] = 0
        self.scope_stack.append((scope, scope_id))

    def exit_scope(self, scope: PythonScope):
        if self.scope_counters:
            _, scope_id = self.scope_stack.pop()
            self.scope_counters.pop(scope_id)

    # TODO: Ideally this is not needed. For safety and readability.
    def _scope_symbol(self, scope: PythonScope) -> str:
        if isinstance(scope, ast.Module):
            return "m"
        elif isinstance(scope, ast.ClassDef):
            return "c"
        elif isinstance(scope, ast.FunctionDef):
            return "f"
        else:
            raise ValueError(f"Unknown scope type: {type(scope)}")

    def _get_next_id(self) -> str:
        _, scope_id = self.scope_stack[-1]
        count = self.scope_counters[scope_id]
        self.scope_counters[scope_id] = count + 1
        return f"{scope_id}_{count}"

    def new_func_literal_name(self) -> str:
        scope_id = self._get_next_id()
        return f"{typhon_prefix}fn_{scope_id}"

    def new_variable_rename_name(self, original_name: str) -> str:
        scope_id = self._get_next_id()
        return f"{typhon_prefix}vr_{scope_id}_{original_name}"

    def new_const_rename_name(self, original_name: str) -> str:
        scope_id = self._get_next_id()
        return f"{typhon_prefix}cn_{scope_id}_{original_name}"

    def new_arrow_type_name(self) -> str:
        scope_id = self._get_next_id()
        return f"{typhon_prefix}ar_{scope_id}"
