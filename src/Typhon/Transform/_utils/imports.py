from ...Grammar.typhon_ast import (
    PosAttributes,
    add_import_alias_top,
    set_is_internal_name,
)
from ..name_generator import (
    get_protocol_name,
    get_final_name,
    get_dataclass_name,
    get_runtime_checkable_name,
)
import ast
from typing import Unpack


def _add_import_for_protocol(mod: ast.Module):
    name = get_protocol_name()
    add_import_alias_top(mod, "typing", "Protocol", name)
    return name


def get_protocol(
    mod: ast.Module, ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]
) -> ast.Name:
    protocol_name = _add_import_for_protocol(mod)
    return set_is_internal_name(ast.Name(id=protocol_name, ctx=ctx, **kwargs))


def add_import_for_final(mod: ast.Module):
    name = get_final_name()
    add_import_alias_top(mod, "typing", "Final", name)
    return name


def get_final(ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]) -> ast.Name:
    final_name = get_final_name()
    return set_is_internal_name(ast.Name(id=final_name, ctx=ctx, **kwargs))


def get_final_of_type(
    type_expr: ast.expr | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if type_expr is None:
        return get_final(ctx=ast.Load(), **kwargs)
    return ast.Subscript(
        value=get_final(ctx=ast.Load(), **kwargs),
        slice=type_expr,
        ctx=ast.Load(),
        **kwargs,
    )


def add_import_get_final(
    mod: ast.Module, ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]
) -> ast.Name:
    final_name = add_import_for_final(mod)
    return set_is_internal_name(ast.Name(id=final_name, ctx=ctx, **kwargs))


def _add_import_for_dataclass(mod: ast.Module):
    name = get_dataclass_name()
    add_import_alias_top(mod, "dataclasses", "dataclass", name)
    return name


def get_dataclass(
    mod: ast.Module, ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]
) -> ast.Name:
    dataclass_name = _add_import_for_dataclass(mod)
    return set_is_internal_name(ast.Name(id=dataclass_name, ctx=ctx, **kwargs))


def _add_import_for_runtime_checkable(mod: ast.Module):
    name = get_runtime_checkable_name()
    add_import_alias_top(mod, "typing", "runtime_checkable", name)
    return name


def get_runtime_checkable(
    mod: ast.Module, ctx: ast.expr_context, **kwargs: Unpack[PosAttributes]
) -> ast.Name:
    runtime_checkable_name = _add_import_for_runtime_checkable(mod)
    return set_is_internal_name(ast.Name(id=runtime_checkable_name, ctx=ctx, **kwargs))


def get_insert_point_for_class(module: ast.Module) -> int:
    for index, stmt in enumerate(module.body):
        if not isinstance(stmt, (ast.Import, ast.ImportFrom)):
            return index
    return len(module.body)
