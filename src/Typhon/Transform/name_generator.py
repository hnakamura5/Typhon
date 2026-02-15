import ast
from typing import Union
from enum import Enum, auto
from contextlib import contextmanager
from ..Grammar.typhon_ast import (
    get_generated_name_original_map,
    add_generated_name_original,
)


typhon_prefix = "_typh_"
typhon_builtin_prefix = f"{typhon_prefix}bi_"

PythonScope = Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]


# TODO Namekind Enum
class NameKind(Enum):
    VARIABLE = auto()
    CONST = auto()
    ARGUMENT = auto()
    FUNCTION_LITERAL = auto()
    CONTROL_COMPREHENSION = auto()
    ARROW_TYPE = auto()
    CLASS = auto()
    FUNCTION = auto()
    IMPORT = auto()
    TYPEVAR = auto()
    OTHER = auto()


def get_protocol_name() -> str:
    return f"{typhon_builtin_prefix}Protocol"


def get_final_name() -> str:
    return f"{typhon_builtin_prefix}Final"


def get_unwrap_name() -> str:
    return f"{typhon_builtin_prefix}unwrap"


def get_unwrap_error_name() -> str:
    return "ValueError"  # TODO: Should be special error?


def get_dataclass_name() -> str:
    return f"{typhon_builtin_prefix}dataclass"


def get_runtime_checkable_name() -> str:
    return f"{typhon_builtin_prefix}runtime_checkable"


_SCOPE_COUNTER = "_typh_name_generator_scope_counters"
_SCOPE_IDS = "_typh_name_generator_scope_ids"


class UniqueNameGenerator:
    _module: ast.Module
    scope_ids: dict[PythonScope, str] = {}
    counter_in_scope: dict[str, int]
    scope_stack: list[tuple[PythonScope, str]] = []
    generated_name_map: dict[str, str]

    def __init__(self, module: ast.Module):
        self._module = module
        self.scope_ids = self._module_scope_ids(module)
        self.counter_in_scope = self._module_scope_counter(module)
        self.generated_name_map = get_generated_name_original_map(module)

    # To use consistent scope counters across multiple passes on the same module.
    def _module_scope_counter(self, module: ast.Module) -> dict[str, int]:
        attr_name = _SCOPE_COUNTER
        scope_counters: dict[str, int] | None = getattr(module, attr_name, None)
        if scope_counters is None:
            scope_counters = {}
            setattr(module, attr_name, scope_counters)
        return scope_counters

    def _module_scope_ids(self, module: ast.Module) -> dict[PythonScope, str]:
        attr_name = _SCOPE_IDS
        scope_id_counter: dict[PythonScope, str] | None = getattr(
            module, attr_name, None
        )
        if scope_id_counter is None:
            scope_id_counter = {}
            setattr(module, attr_name, scope_id_counter)
        return scope_id_counter

    # Here the scope is Python scope: module, class, function. Not block scope.
    def enter_scope(self, scope: PythonScope):
        scope_id = self.scope_ids.get(scope, None)
        if scope_id is None:
            index = len(self.scope_ids)
            scope_id = f"{self._scope_symbol(scope)}{index}"
            self.scope_ids[scope] = scope_id
            self.counter_in_scope[scope_id] = 0
        self.scope_stack.append((scope, scope_id))

    def exit_scope(self, scope: PythonScope):
        self.scope_stack.pop()

    @contextmanager
    def name_scope(self, scope: PythonScope):
        self.enter_scope(scope)
        yield
        self.exit_scope(scope)

    # TODO: Ideally this is not needed. For safety and readability.
    def _scope_symbol(self, scope: PythonScope) -> str:
        if isinstance(scope, ast.Module):
            return "m"
        elif isinstance(scope, ast.ClassDef):
            return "c"
        else:
            return "f"

    def _get_next_id(self) -> str:
        _, scope_id = self.scope_stack[-1]
        count = self.counter_in_scope[scope_id]
        self.counter_in_scope[scope_id] = count + 1
        return f"{scope_id}_{count}"

    def _new_name(self, kind: NameKind, original_name: str = "") -> str:
        if kind == NameKind.VARIABLE:
            return f"{typhon_prefix}vr_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.CONST:
            return f"{typhon_prefix}cn_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.ARGUMENT:
            return f"{typhon_prefix}ag_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.FUNCTION_LITERAL:
            return f"{typhon_prefix}fn_{self._get_next_id()}"
        elif kind == NameKind.CONTROL_COMPREHENSION:
            return f"{typhon_prefix}cc_{self._get_next_id()}"
        elif kind == NameKind.ARROW_TYPE:
            return f"{typhon_prefix}ar_{self._get_next_id()}"
        elif kind == NameKind.CLASS:
            return f"{typhon_prefix}cl_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.FUNCTION:
            return f"{typhon_prefix}df_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.IMPORT:
            return f"{typhon_prefix}im_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.TYPEVAR:
            return f"{typhon_prefix}tv_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.OTHER:
            return f"{typhon_prefix}ot_{self._get_next_id()}_{original_name}"
        else:
            raise ValueError(f"Unknown NameKind: {kind}")

    def new_name(self, kind: NameKind, original_name: str = "") -> str:
        result = self._new_name(kind, original_name)
        if result in self.generated_name_map:
            raise SyntaxError(f"Generated name conflict: {result}")
        add_generated_name_original(self._module, result, original_name)
        return result
