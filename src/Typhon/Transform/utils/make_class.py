from ...Driver.debugging import debug_print
from ...Grammar.typhon_ast import (
    get_pos_attributes,
    pos_attribute_to_range,
    set_is_var,
    PosAttributes,
)
import ast
from typing import Protocol, Iterable, Final
from .imports import (
    add_import_for_dataclass,
    add_import_for_protocol,
    add_import_for_runtime_checkable,
    add_import_for_final,
)


class NameAndAnnotation(Protocol):
    name: Final[ast.Name]
    annotation: Final[ast.expr]


def _class_contents_for_fields(
    fields: Iterable[NameAndAnnotation],
    final_imported_name: str,
) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for field in fields:
        name = field.name
        if field.annotation:
            # Currently annotation is always Final[...] for record fields.
            annotation = ast.Subscript(
                value=ast.Name(
                    id=final_imported_name, ctx=ast.Load(), **get_pos_attributes(name)
                ),
                slice=field.annotation,
                ctx=ast.Load(),
                **get_pos_attributes(name),
            )
        else:
            annotation = ast.Name(
                id=final_imported_name, ctx=ast.Load(), **get_pos_attributes(name)
            )
        ann_assign = ast.AnnAssign(
            target=ast.Name(id=name.id, ctx=ast.Store(), **get_pos_attributes(name)),
            annotation=annotation,
            value=None,
            simple=1,
            **get_pos_attributes(name),
        )
        # "var" because dataclass is frozen, "Final" is not required.
        set_is_var(ann_assign)
        result.append(ann_assign)
    return result


def _type_vars_for_fields(
    pos: PosAttributes, type_variables: list[str]
) -> list[ast.type_param]:
    type_params: list[ast.type_param] = []
    for tv in type_variables:
        type_params.append(ast.TypeVar(name=tv, **pos_attribute_to_range(pos)))
    return type_params


def make_protocol_definition(
    mod: ast.Module,
    class_name: str,
    type_variables: list[str],
    fields: Iterable[NameAndAnnotation],
    pos: PosAttributes,
) -> ast.ClassDef:
    protocol_imported_name: str = add_import_for_protocol(mod)
    runtime_checkable_imported_name: str = add_import_for_runtime_checkable(mod)
    final_imported_name: str = add_import_for_final(mod)
    result = ast.ClassDef(
        name=class_name,
        type_params=_type_vars_for_fields(pos, type_variables),
        bases=[ast.Name(id=protocol_imported_name, ctx=ast.Load(), **pos)],
        keywords=[],
        # Currently all fields are Final.
        body=_class_contents_for_fields(fields, final_imported_name),
        decorator_list=[
            ast.Name(id=runtime_checkable_imported_name, ctx=ast.Load(), **pos)
        ],
        **pos,
    )
    return result


def _dataclass_decorator(
    dataclass_imported_name: str, repr: bool, pos: PosAttributes
) -> ast.expr:
    return ast.Call(
        func=ast.Name(id=dataclass_imported_name, ctx=ast.Load(), **pos),
        args=[],
        keywords=[
            ast.keyword(arg="frozen", value=ast.Constant(value=True)),
            ast.keyword(arg="repr", value=ast.Constant(value=repr)),
            ast.keyword(arg="unsafe_hash", value=ast.Constant(value=True)),
            ast.keyword(arg="kw_only", value=ast.Constant(value=True)),
        ],
    )


def make_dataclass_definition(
    mod: ast.Module,
    class_name: str,
    type_variables: list[str],
    fields: Iterable[NameAndAnnotation],
    pos: PosAttributes,
) -> ast.ClassDef:
    dataclass_imported_name: str = add_import_for_dataclass(mod)
    final_imported_name: str = add_import_for_final(mod)
    result = ast.ClassDef(
        name=class_name,
        type_params=_type_vars_for_fields(pos, type_variables),
        bases=[],
        keywords=[],
        body=_class_contents_for_fields(fields, final_imported_name),
        decorator_list=[
            _dataclass_decorator(dataclass_imported_name, repr=False, pos=pos)
        ],
        **pos,
    )
    return result


def make_dataclass_protocol_definition(
    mod: ast.Module,
    class_name: str,
    type_variables: list[str],
    fields: Iterable[NameAndAnnotation],
    pos: PosAttributes,
) -> ast.ClassDef:
    dataclass_imported_name: str = add_import_for_dataclass(mod)
    result = make_protocol_definition(mod, class_name, type_variables, fields, pos)
    result.decorator_list.append(
        _dataclass_decorator(dataclass_imported_name, repr=True, pos=pos)
    )
    return result
