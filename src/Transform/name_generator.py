import ast
from typing import Union, Any, Literal
from enum import Enum, auto
from contextlib import contextmanager


typhon_prefix = "_typh_"
typhon_builtin_prefix = f"{typhon_prefix}bi_"

PythonScope = Union[ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]


# TODO Namekind Enum
class NameKind(Enum):
    VARIABLE = auto()
    CONST = auto()
    ARGUMENT = auto()
    FUNCTION_LITERAL = auto()
    ARROW_TYPE = auto()
    CLASS = auto()
    FUNCTION = auto()
    IMPORT = auto()
    OTHER = auto()


def get_protocol_name() -> str:
    return f"{typhon_builtin_prefix}Protocol"


def get_final_name() -> str:
    return f"{typhon_builtin_prefix}Final"


def get_unwrap_name() -> str:
    return f"{typhon_builtin_prefix}unwrap"


def get_unwrap_error_name() -> str:
    return "ValueError"  # TODO: Should be special error?


class UniqueNameGenerator:
    scope_id_counter: int
    scope_stack: list[tuple[PythonScope, str]] = []
    scope_counters: dict[str, int]
    generated_names: set[str]

    def __init__(self, module: ast.Module):
        self.scope_id_counter = 0
        self.scope_counters = self._module_scope_counter(module)
        self.generated_names = self._module_generated_names(module)

    # To use consistent scope counters across multiple passes on the same module.
    def _module_scope_counter(self, module: ast.Module) -> dict[str, int]:
        attr_name = "_typh_name_generator_scope_counters"
        scope_counters: dict[str, int] | None = getattr(module, attr_name, None)
        if scope_counters is None:
            scope_counters = {}
            setattr(module, attr_name, scope_counters)
        return scope_counters

    def _module_generated_names(self, module: ast.Module) -> set[str]:
        attr_name = "_typh_name_generator_generated_names"
        generated_names: set[str] | None = getattr(module, attr_name, None)
        if generated_names is None:
            generated_names = set()
            setattr(module, attr_name, generated_names)
        return generated_names

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
        elif isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            return "f"
        else:
            raise ValueError(f"Unknown scope type: {type(scope)}")

    def _get_next_id(self) -> str:
        _, scope_id = self.scope_stack[-1]
        count = self.scope_counters[scope_id]
        self.scope_counters[scope_id] = count + 1
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
        elif kind == NameKind.ARROW_TYPE:
            return f"{typhon_prefix}ar_{self._get_next_id()}"
        elif kind == NameKind.CLASS:
            return f"{typhon_prefix}cl_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.FUNCTION:
            return f"{typhon_prefix}df_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.IMPORT:
            return f"{typhon_prefix}im_{self._get_next_id()}_{original_name}"
        elif kind == NameKind.OTHER:
            return f"{typhon_prefix}ot_{self._get_next_id()}_{original_name}"
        else:
            raise ValueError(f"Unknown NameKind: {kind}")

    def new_name(self, kind: NameKind, original_name: str = "") -> str:
        result = self._new_name(kind, original_name)
        if result in self.generated_names:
            raise SyntaxError(f"Generated name conflict: {result}")
        self.generated_names.add(result)
        return result
