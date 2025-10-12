import ast
from ..Grammar.typhon_ast import (
    RecordLiteral,
    get_record_literal_fields,
    get_record_type_fields,
    get_pos_attributes,
    pos_attribute_noneless,
    get_empty_pos_attributes,
    PosAttributes,
    set_is_var,
    is_record_literal,
    is_record_type,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from .utils import (
    add_import_for_dataclass,
    add_import_for_protocol,
    add_import_for_runtime_checkable,
    add_import_for_final,
    get_insert_point_for_class,
)
from dataclasses import dataclass
from typing import Protocol, Iterable


class NameAndAnnotation(Protocol):
    name: ast.Name
    annotation: ast.expr


@dataclass
class RecordFieldInfo:
    name: ast.Name
    annotation: ast.expr
    value: ast.expr


@dataclass
class RecordInfo:
    record: RecordLiteral
    class_name: str
    fields: list[RecordFieldInfo]
    type_variables: list[str]


@dataclass
class RecordTypeFieldInfo:
    name: ast.Name
    annotation: ast.expr
    orig_annotation: ast.expr


@dataclass
class RecordTypeInfo:
    record: RecordLiteral
    class_name: str
    fields: list[RecordTypeFieldInfo]
    type_variables: list[str]


class _GatherRecords(TyphonASTVisitor):
    records: list[RecordInfo]
    record_types: list[RecordTypeInfo]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.records = []
        self.record_types = []

    def _visit_RecordLiteral(self, node: RecordLiteral):
        fields = get_record_literal_fields(node)
        if not fields:
            return
        type_vars: list[str] = []
        field_infos: list[RecordFieldInfo] = []
        for name, annotation, value in fields:
            if not annotation:
                type_var = self.new_typevar_name(name.id)
                type_vars.append(type_var)
                annotation = ast.Name(
                    id=type_var, ctx=ast.Load(), **get_pos_attributes(name)
                )
            field_infos.append(RecordFieldInfo(name, annotation, value))
        self.records.append(
            RecordInfo(node, self.new_class_name(""), field_infos, type_vars)
        )

    def _visit_RecordType(self, node: RecordLiteral):
        type_fields = get_record_type_fields(node)
        if not type_fields:
            return
        type_vars = []
        field_infos: list[RecordTypeFieldInfo] = []
        for name, annotation in type_fields:
            # Always create a new type variable for each field so that scoped type
            # variables are handled correctly.
            type_var = self.new_typevar_name(name.id)
            type_vars.append(type_var)
            field_infos.append(
                RecordTypeFieldInfo(
                    name,
                    # Use the type variable as the annotation.
                    ast.Name(id=type_var, ctx=ast.Load(), **get_pos_attributes(name)),
                    # And pass the original annotation as parameter.
                    annotation,
                )
            )
        self.record_types.append(
            RecordTypeInfo(node, self.new_class_name(""), field_infos, type_vars)
        )

    def visit_Name(self, node: RecordLiteral):
        if is_record_literal(node):
            self._visit_RecordLiteral(node)
        elif is_record_type(node):
            self._visit_RecordType(node)
        return self.generic_visit(node)


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


def _class_contents_for_fields(
    fields: Iterable[NameAndAnnotation],
    type_variables: list[str],
    final_imported_name: str,
) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for field in fields:
        name = field.name
        annotation = ast.Subscript(
            value=ast.Name(
                id=final_imported_name, ctx=ast.Load(), **get_pos_attributes(name)
            ),
            slice=field.annotation,
            ctx=ast.Load(),
            **get_pos_attributes(name),
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
    record: ast.Name, type_variables: list[str]
) -> list[ast.type_param]:
    type_params: list[ast.type_param] = []
    for tv in type_variables:
        type_params.append(
            ast.TypeVar(name=tv, **pos_attribute_noneless(get_pos_attributes(record)))
        )
    return type_params


def _add_repr_to_dataclass(
    class_def: ast.ClassDef, record: ast.Name, fields: Iterable[NameAndAnnotation]
):
    repr_values: list[ast.expr] = []
    repr_values.append(ast.Constant(value="{|", **get_pos_attributes(record)))
    for field in fields:
        repr_values.append(
            ast.Constant(value=f"{field.name.id}=", **get_pos_attributes(field.name))
        )
        repr_values.append(
            ast.FormattedValue(
                value=ast.Attribute(
                    value=ast.Name(
                        id="self", ctx=ast.Load(), **get_pos_attributes(field.name)
                    ),
                    attr=field.name.id,
                    ctx=ast.Load(),
                    **get_pos_attributes(field.name),
                ),
                conversion=b"r"[0],  # !r conversion
                format_spec=None,
            )
        )
        repr_values.append(ast.Constant(value=", ", **get_pos_attributes(field.name)))
    if len(repr_values) > 1:
        repr_values.pop()  # Remove the last comma
    repr_values.append(ast.Constant(value="|}", **get_pos_attributes(record)))
    # __repr__ method return the f-string.
    repr_func_def = ast.FunctionDef(
        name="__repr__",
        args=ast.arguments(),
        body=[
            ast.Return(
                value=ast.JoinedStr(values=repr_values, **get_pos_attributes(record)),
                **get_pos_attributes(record),
            )
        ],
        **get_pos_attributes(record),
    )
    class_def.body.append(repr_func_def)


def _make_dataclass_definition(
    info: RecordInfo,
    dataclass_imported_name: str,
    final_imported_name: str,
) -> ast.ClassDef:
    result = ast.ClassDef(
        name=info.class_name,
        type_params=_type_vars_for_fields(info.record, info.type_variables),
        bases=[],
        keywords=[],
        body=_class_contents_for_fields(
            info.fields, info.type_variables, final_imported_name
        ),
        decorator_list=[
            _dataclass_decorator(
                dataclass_imported_name, repr=False, pos=get_pos_attributes(info.record)
            )
        ],
        **get_pos_attributes(info.record),
    )
    _add_repr_to_dataclass(result, info.record, info.fields)
    return result


def _make_dataclass_protocol_definition(
    info: RecordTypeInfo,
    dataclass_imported_name: str,
    protocol_imported_name: str,
    runtime_checkable_imported_name: str,
    final_imported_name: str,
) -> ast.ClassDef:
    result = ast.ClassDef(
        name=info.class_name,
        type_params=_type_vars_for_fields(info.record, info.type_variables),
        bases=[
            ast.Name(
                id=protocol_imported_name,
                ctx=ast.Load(),
                **get_pos_attributes(info.record),
            )
        ],
        keywords=[],
        body=_class_contents_for_fields(
            info.fields, info.type_variables, final_imported_name
        ),
        decorator_list=[
            ast.Name(
                id=runtime_checkable_imported_name,
                ctx=ast.Load(),
                **get_pos_attributes(info.record),
            ),
            _dataclass_decorator(
                dataclass_imported_name, repr=True, pos=get_pos_attributes(info.record)
            ),
        ],
        **get_pos_attributes(info.record),
    )
    return result


class _Transform(TyphonASTTransformer):
    def __init__(
        self,
        module: ast.Module,
        class_for_record: dict[ast.Name, ast.ClassDef],
        info_for_record: dict[ast.Name, RecordInfo],
        class_for_record_type: dict[ast.Name, ast.ClassDef],
        info_for_record_type: dict[ast.Name, RecordTypeInfo],
    ):
        super().__init__(module)
        self.class_for_record = class_for_record
        self.info_for_record = info_for_record
        self.class_for_record_type = class_for_record_type
        self.info_for_record_type = info_for_record_type

    def visit_Name(self, node: ast.Name):
        if node in self.class_for_record:
            class_def = self.class_for_record[node]
            pos = get_pos_attributes(node)
            return ast.Call(
                func=ast.Name(id=class_def.name, ctx=ast.Load(), **pos),
                args=[],
                keywords=[
                    ast.keyword(
                        arg=field.name.id,
                        value=field.value,
                        **get_pos_attributes(field.name),
                    )
                    for field in self.info_for_record[node].fields
                ],
                **pos,
            )
        elif node in self.class_for_record_type:
            class_def = self.class_for_record_type[node]
            info = self.info_for_record_type[node]
            return ast.Subscript(
                value=ast.Name(
                    id=class_def.name, ctx=ast.Load(), **get_pos_attributes(node)
                ),
                slice=ast.Tuple(
                    elts=[field.orig_annotation for field in info.fields],
                    ctx=ast.Load(),
                    **get_empty_pos_attributes(),
                ),
            )
        return self.generic_visit(node)


# Run before other transformations so that the generated call is visited properly.
def record_to_dataclass(module: ast.Module):
    gatherer = _GatherRecords(module)
    gatherer.run()
    if not gatherer.records and not gatherer.record_types:
        return
    # Add imports
    dataclass_imported_name = add_import_for_dataclass(module)
    final_imported_name = add_import_for_final(module)
    protocol_imported_name = ""
    runtime_checkable_imported_name = ""
    if gatherer.record_types:
        protocol_imported_name = add_import_for_protocol(module)
        runtime_checkable_imported_name = add_import_for_runtime_checkable(module)
    # Create class and information for each record literal.
    class_for_record: dict[ast.Name, ast.ClassDef] = {}
    info_for_record: dict[ast.Name, RecordInfo] = {}
    insert_point = get_insert_point_for_class(module)
    for info in gatherer.records:
        class_def = _make_dataclass_definition(
            info,
            dataclass_imported_name,
            final_imported_name,
        )
        class_for_record[info.record] = class_def
        info_for_record[info.record] = info
        module.body.insert(insert_point, class_def)
        insert_point += 1
    # Create class and information for each record type.
    class_for_record_type: dict[ast.Name, ast.ClassDef] = {}
    info_for_record_type: dict[ast.Name, RecordTypeInfo] = {}
    if gatherer.record_types:
        for info in gatherer.record_types:
            class_def_type = _make_dataclass_protocol_definition(
                info,
                dataclass_imported_name,
                protocol_imported_name,
                runtime_checkable_imported_name,
                final_imported_name,
            )
            class_for_record_type[info.record] = class_def_type
            info_for_record_type[info.record] = info
            module.body.insert(insert_point, class_def_type)
            insert_point += 1
    _Transform(
        module,
        class_for_record,
        info_for_record,
        class_for_record_type,
        info_for_record_type,
    ).run()
    print(f"dump module after record_to_dataclass: {ast.dump(module)}")
