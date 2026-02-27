from ...Grammar.typhon_ast import (
    get_pos_attributes,
    pos_attribute_to_range,
    set_is_internal_name,
    set_is_var,
    PosAttributes,
)
import ast
from typing import Protocol, Iterable, Final
from .imports import (
    get_dataclass,
    add_import_get_final,
    get_protocol,
    get_runtime_checkable,
)


class NameAndAnnotation(Protocol):
    name: Final[ast.Name]
    annotation: Final[ast.expr]


def _class_contents_for_fields(
    fields: Iterable[NameAndAnnotation],
    final_imported_name: ast.Name,
) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for field in fields:
        name = field.name
        if field.annotation:
            # Currently annotation is always Final[...] for record fields.
            annotation = ast.Subscript(
                value=final_imported_name,
                slice=field.annotation,
                ctx=ast.Load(),
                **get_pos_attributes(name),
            )
        else:
            annotation = final_imported_name
        ann_assign = ast.AnnAssign(
            target=set_is_internal_name(
                ast.Name(id=name.id, ctx=ast.Store(), **get_pos_attributes(name))
            ),
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
    protocol_imported_name = get_protocol(mod, ctx=ast.Load(), **pos)
    runtime_checkable_imported_name = get_runtime_checkable(mod, ctx=ast.Load(), **pos)
    final_imported_name = add_import_get_final(mod, ctx=ast.Load(), **pos)
    result = ast.ClassDef(
        name=class_name,
        type_params=_type_vars_for_fields(pos, type_variables),
        bases=[protocol_imported_name],
        keywords=[],
        # Currently all fields are Final.
        body=_class_contents_for_fields(fields, final_imported_name),
        decorator_list=[runtime_checkable_imported_name],
        **pos,
    )
    return result


def _dataclass_decorator(
    dataclass_imported_name: ast.Name, repr: bool, pos: PosAttributes
) -> ast.expr:
    return ast.Call(
        func=dataclass_imported_name,
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
    dataclass_imported_name = get_dataclass(mod, ctx=ast.Load(), **pos)
    final_imported_name = add_import_get_final(mod, ctx=ast.Load(), **pos)
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
    dataclass_imported_name = get_dataclass(mod, ctx=ast.Load(), **pos)
    result = make_protocol_definition(mod, class_name, type_variables, fields, pos)
    result.decorator_list.append(
        _dataclass_decorator(dataclass_imported_name, repr=True, pos=pos)
    )
    return result
