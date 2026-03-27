import ast
import base64
import hashlib
from dataclasses import dataclass
from enum import Enum, auto
from contextlib import contextmanager
from ..Grammar.typhon_ast import (
    get_generated_name_original_map,
    add_generated_name_original,
    PythonScope,
)


_TYPHON_PREFIX = "_typh_"
_TYPHON_BUILTIN_PREFIX = f"{_TYPHON_PREFIX}bi_"


def is_reserved_typh_name(name: str) -> bool:
    return name.startswith(_TYPHON_PREFIX)


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


def _kind_code(kind: NameKind) -> str:
    if kind == NameKind.VARIABLE:
        return "v"
    elif kind == NameKind.CONST:
        return "c"
    elif kind == NameKind.ARGUMENT:
        return "a"
    elif kind == NameKind.FUNCTION_LITERAL:
        return "lf"
    elif kind == NameKind.CONTROL_COMPREHENSION:
        return "cc"
    elif kind == NameKind.ARROW_TYPE:
        return "ar"
    elif kind == NameKind.CLASS:
        return "cl"
    elif kind == NameKind.FUNCTION:
        return "df"
    elif kind == NameKind.IMPORT:
        return "im"
    elif kind == NameKind.TYPEVAR:
        return "tv"
    elif kind == NameKind.OTHER:
        return "ot"
    else:
        raise ValueError(f"Unknown NameKind: {kind}")


def is_builtin_name(name: str) -> bool:
    return name.startswith(_TYPHON_BUILTIN_PREFIX)


def get_protocol_name() -> str:
    return f"{_TYPHON_BUILTIN_PREFIX}Protocol"


def get_final_name() -> str:
    return f"{_TYPHON_BUILTIN_PREFIX}Final"


def get_unwrap_name() -> str:
    return f"{_TYPHON_BUILTIN_PREFIX}unwrap"


def get_unwrap_error_name() -> str:
    return "ValueError"  # TODO: Should be special error?


def get_dataclass_name() -> str:
    return f"{_TYPHON_BUILTIN_PREFIX}dataclass"


def get_runtime_checkable_name() -> str:
    return f"{_TYPHON_BUILTIN_PREFIX}runtime_checkable"


_RAW_SCOPE_ID_COUNTER = "_typh_name_generator_scope_counters"
_SCOPE_IDS = "_typh_name_generator_scope_ids"
_SCOPE_COUNT_COUNTER = "_typh_name_generator_scope_count"
_MANGLE_COLLISION_COUNTER = "_typh_name_generator_collision_counter"


@dataclass(frozen=True)
class MangleHashSeed:
    kind: NameKind
    node_id: str
    scope_id: str
    original_name: str = ""

    def serialize(self) -> str:
        return "$".join(
            [
                self.kind.name,
                self.scope_id,
                self.node_id,
                self.original_name,
            ]
        )

    def short_hash(self) -> str:
        text: str = self.serialize()
        digest = hashlib.blake2b(text.encode("utf-8"), digest_size=5).digest()
        return base64.b32encode(digest).decode("ascii").rstrip("=").lower()


# The goal of name mangling:
# - Make unique name in determistic way.
# - The name is as stable as possible across small code change.
# - Especially stable per Function, that is re-parse unit in most cases(but for top-level statement).
# Mangling string is hash of scope_id and kind_id.
# - scope_id is based on the scope (Class, Function, Module) signature.
# - kind_id is based on the NameKind, original_name and its visited order in the scope.
# The visiting order is determined by the AST traversal, which is stable as far as new nodes with
# the kind are not added before the anchored node in the same scope.
# At top lebel, the scope is module but the re-parse unit is the outermost statement. In this case,
# name is not saved in PythonScope, hence this may be stable.
# This is current limitation, when the same original name is used multiple times.
class UniqueNameGenerator:
    _module: ast.Module
    scope_ids: dict[PythonScope, str] = {}
    scope_kind_counter: dict[PythonScope, dict[str, int]] = {}
    raw_scope_id_counter: dict[str, int]
    scope_stack: list[tuple[PythonScope, str]] = []
    generated_name_map: dict[str, str]
    collision_counter: dict[str, int]

    def __init__(self, module: ast.Module):
        self._module = module
        self.scope_ids = self._module_scope_ids(module)
        self.scope_kind_counter = self._module_scope_kind_counter(module)
        self.raw_scope_id_counter = self._module_raw_scope_id_counter(module)
        self.generated_name_map = get_generated_name_original_map(module)
        self.collision_counter = self._module_collision_counter(module)

    def _module_attr_get_or_init[T](self, attr_name: str, init_value: T) -> T:
        value = getattr(self._module, attr_name, None)
        if value is None:
            setattr(self._module, attr_name, init_value)
            return init_value
        return value

    # To use consistent scope counters across multiple passes on the same module.
    def _module_raw_scope_id_counter(self, module: ast.Module) -> dict[str, int]:
        return self._module_attr_get_or_init(_RAW_SCOPE_ID_COUNTER, {})

    def _module_scope_ids(self, module: ast.Module) -> dict[PythonScope, str]:
        return self._module_attr_get_or_init(_SCOPE_IDS, {})

    def _module_scope_kind_counter(
        self, module: ast.Module
    ) -> dict[PythonScope, dict[str, int]]:
        return self._module_attr_get_or_init(_SCOPE_COUNT_COUNTER, {})

    def _module_collision_counter(self, module: ast.Module) -> dict[str, int]:
        return self._module_attr_get_or_init(_MANGLE_COLLISION_COUNTER, {})

    # Here the scope is Python scope: module, class, function. Not block scope.
    def enter_scope(self, scope: PythonScope):
        scope_id = self._get_scope_id(scope)
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
        count = self.raw_scope_id_counter[scope_id]
        self.raw_scope_id_counter[scope_id] = count + 1
        return f"{scope_id}_{count}"

    def _parent_scope(self) -> PythonScope:
        if len(self.scope_stack) >= 1:
            return self.scope_stack[-1][0]
        return self._module

    def _parent_scope_id(self) -> str:
        if len(self.scope_stack) >= 1:
            return self.scope_stack[-1][1]
        return self._get_scope_id(self._module)

    def _header_shape(self, scope: PythonScope) -> str:
        if isinstance(scope, ast.ClassDef):
            return (
                f"cls|ba={len(scope.bases)}|kw={len(scope.keywords)}|"
                f"tp={len(scope.type_params or [])}"
            )
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = scope.args
            return (
                f"fn|as={int(isinstance(scope, ast.AsyncFunctionDef))}|"
                f"po={len(args.posonlyargs)}|a={len(args.args)}|"
                f"ko={len(args.kwonlyargs)}|va={int(args.vararg is not None)}|"
                f"ka={int(args.kwarg is not None)}|tp={len(scope.type_params or [])}"
            )
        return "module"

    # Actually, not necessarily "id". Distinguish almost all scopes independent from order or position.
    def _get_scope_id(self, scope: PythonScope) -> str:
        if scope_id := self.scope_ids.get(scope):
            return scope_id
        if isinstance(scope, ast.Module):
            raw_scope_id = "m"
        else:  # Class and Function
            parent_scope_id = self._parent_scope_id()
            # Header shape is stable. Has few risk of collision.
            raw_scope_id = f"{parent_scope_id}/{scope.name}|{self._header_shape(scope)}"
        if raw_scope_id in self.raw_scope_id_counter:
            scope_id = f"{raw_scope_id}@{self.raw_scope_id_counter[raw_scope_id]}"
        else:
            scope_id = raw_scope_id
            self.raw_scope_id_counter.setdefault(raw_scope_id, 0)
        self.scope_ids[scope] = scope_id
        self.raw_scope_id_counter[raw_scope_id] += 1
        return scope_id

    # Actually, not "id". The key is kind and collision counting.
    # This is enough to avoid the effect of small change in expression.
    def _anchor_id_from_node(
        self, node: ast.AST, kind: NameKind, original_name: str
    ) -> str:
        candidate = f"{kind.name}_{original_name}"
        parent = self._parent_scope()
        kind_counter = self.scope_kind_counter.setdefault(parent, {})
        count = kind_counter.setdefault(candidate, 0)
        kind_counter[candidate] = count + 1
        return f"{kind.name}_{count}"

    def _seed_with_anchored_node(
        self,
        node: ast.AST,
        *,
        original_name: str,
        kind: NameKind,
        scope: PythonScope | None = None,
    ) -> MangleHashSeed:
        scope_id = (
            self._get_scope_id(scope) if scope is not None else self._parent_scope_id()
        )
        node_id = (
            f"{original_name}|{self._anchor_id_from_node(node, kind, original_name)}"
        )
        return MangleHashSeed(
            kind=kind,
            node_id=node_id,
            scope_id=scope_id,
            original_name=original_name,
        )

    def _render_name(self, seed: MangleHashSeed, use_original_name: bool) -> str:
        parts = [
            f"{_TYPHON_PREFIX}{_kind_code(seed.kind)}",
            seed.short_hash(),
        ]
        if use_original_name and seed.original_name:
            parts.append(seed.original_name)
        return "_".join(parts)

    def _new_name_from_seed(self, seed: MangleHashSeed, use_original_name: bool) -> str:
        base_name = self._render_name(seed, use_original_name)
        collision_index = self.collision_counter.get(base_name)
        if collision_index is not None:
            new_name = f"{base_name}_{collision_index}"
            self.collision_counter[base_name] = collision_index + 1
        else:
            new_name = base_name
            self.collision_counter[base_name] = 1
        add_generated_name_original(self._module, new_name, seed.original_name)
        return new_name

    def new_name_decl(
        self,
        kind: NameKind,
        *,
        anchored_node: ast.AST,
        original_name: str = "",
        scope: PythonScope | None = None,
    ) -> str:
        seed = self._seed_with_anchored_node(
            anchored_node,
            original_name=original_name,
            kind=kind,
            scope=scope,
        )
        return self._new_name_from_seed(seed, use_original_name=True)

    def new_name_anonymous(
        self,
        kind: NameKind,
        *,
        anchored_node: ast.AST,
        pretty_name: str = "",
        scope: PythonScope | None = None,
    ) -> str:
        seed = self._seed_with_anchored_node(
            anchored_node,
            original_name=pretty_name,
            kind=kind,
            scope=scope,
        )
        return self._new_name_from_seed(seed, use_original_name=False)
