from ...Grammar.typhon_ast import (
    add_import_alias_top,
    is_case_irrefutable,
    get_pos_attributes,
    pos_attribute_to_range,
    set_is_var,
)
from ..name_generator import (
    get_protocol_name,
    get_final_name,
    get_dataclass_name,
    get_runtime_checkable_name,
)
import ast
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol, Iterable, Final


def add_import_for_protocol(mod: ast.Module):
    name = get_protocol_name()
    add_import_alias_top(mod, "typing", "Protocol", name)
    return name


def add_import_for_final(mod: ast.Module):
    name = get_final_name()
    add_import_alias_top(mod, "typing", "Final", name)
    return name


def add_import_for_dataclass(mod: ast.Module):
    name = get_dataclass_name()
    add_import_alias_top(mod, "dataclasses", "dataclass", name)
    return name


def add_import_for_runtime_checkable(mod: ast.Module):
    name = get_runtime_checkable_name()
    add_import_alias_top(mod, "typing", "runtime_checkable", name)
    return name


def get_insert_point_for_class(module: ast.Module) -> int:
    for index, stmt in enumerate(module.body):
        if not isinstance(stmt, (ast.Import, ast.ImportFrom)):
            return index
    return len(module.body)
