import ast
import keyword
from ..Grammar.typhon_ast import (
    RecordLiteral,
    add_generated_name_original,
    get_record_literal_fields,
    get_record_type_fields,
    get_pos_attributes,
    pos_attribute_to_range,
    get_empty_pos_attributes,
    PosAttributes,
    set_is_internal_name,
    set_is_var,
    is_record_literal,
    is_record_type,
    is_attributes_pattern,
)
from ..Grammar.pretty_printer import (
    pretty_print_expr,
    make_record_literal_demangle_template,
    make_record_type_demangle_template,
    set_record_literal_typevar_fields,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from ._utils.imports import (
    get_insert_point_for_class,
)
from ._utils.make_class import (
    make_dataclass_protocol_definition,
    make_dataclass_definition,
    NameAndAnnotation,
)
from dataclasses import dataclass
from typing import Protocol, Iterable


@dataclass
class RecordFieldInfo:
    name: ast.Name
    annotation: ast.expr
    value: ast.expr
    is_type_var: bool


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
            is_type_var = False
            if not annotation:
                type_var = self.new_typevar_name(name.id)
                type_vars.append(type_var)
                annotation = set_is_internal_name(
                    ast.Name(id=type_var, ctx=ast.Load(), **get_pos_attributes(name))
                )
                is_type_var = True
            field_infos.append(RecordFieldInfo(name, annotation, value, is_type_var))
        class_name = self.new_class_name("")
        self.records.append(
            RecordInfo(
                node,
                class_name,
                field_infos,
                type_vars,
            )
        )
        add_generated_name_original(
            self.module,
            class_name,
            make_record_literal_demangle_template(
                [
                    (
                        field.name.id,
                        pretty_print_expr(field.annotation)
                        if not field.is_type_var
                        else None,
                    )
                    for field in field_infos
                ]
            ),
        )

    def _visit_RecordType(self, node: RecordLiteral):
        type_fields = get_record_type_fields(node)
        if not type_fields:
            return
        type_vars: list[str] = []
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
                    ast.Name(
                        id=type_var, ctx=ast.Load(), **get_pos_attributes(annotation)
                    ),
                    # And pass the original annotation as parameter.
                    annotation,
                )
            )
        class_name = self.new_class_name("")
        self.record_types.append(
            RecordTypeInfo(
                node,
                class_name,
                field_infos,
                type_vars,
            )
        )
        add_generated_name_original(
            self.module,
            class_name,
            make_record_type_demangle_template(
                [field.name.id for field in field_infos]
            ),
        )

    def visit_Name(self, node: RecordLiteral):
        if is_record_literal(node):
            self._visit_RecordLiteral(node)
        elif is_record_type(node):
            self._visit_RecordType(node)
        return self.generic_visit(node)


def _add_repr_to_dataclass(
    class_def: ast.ClassDef, record: ast.Name, fields: Iterable[NameAndAnnotation]
):
    repr_values: list[ast.expr] = []
    for i, field in enumerate(fields):
        if i == 0:
            # Start the string with {|.
            repr_values.append(
                ast.Constant(
                    value="{|" + f"{field.name.id}=", **get_pos_attributes(record)
                )
            )
        else:
            # Otherwise, join with comma.
            repr_values.append(
                ast.Constant(
                    value=f", {field.name.id}=", **get_pos_attributes(field.name)
                )
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
            keywords: list[ast.keyword] = []
            type_var_fields: list[ast.Name] = []
            for field in self.info_for_record[node].fields:
                keywords.append(
                    ast.keyword(
                        arg=field.name.id,
                        value=ast.Name(
                            id=field.name.id,
                            ctx=ast.Load(),
                            **get_pos_attributes(field.name),
                        ),
                        **get_pos_attributes(field.name),
                    )
                )
                if field.is_type_var:
                    type_var_fields.append(field.name)
            class_name = set_is_internal_name(
                ast.Name(id=class_def.name, ctx=ast.Load(), **pos)
            )
            if type_var_fields:
                set_record_literal_typevar_fields(class_name, type_var_fields)
            return ast.Call(
                func=class_name,
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
                value=set_is_internal_name(
                    ast.Name(
                        id=class_def.name, ctx=ast.Load(), **get_pos_attributes(node)
                    )
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
    # Create class and information for each record literal.
    class_for_record: dict[ast.Name, ast.ClassDef] = {}
    info_for_record: dict[ast.Name, RecordInfo] = {}
    for info in gatherer.records:
        class_def = make_dataclass_definition(
            module,
            info.class_name,
            info.type_variables,
            info.fields,
            get_pos_attributes(info.record),
        )
        _add_repr_to_dataclass(class_def, info.record, info.fields)
        class_for_record[info.record] = class_def
        info_for_record[info.record] = info
        module.body.insert(get_insert_point_for_class(module), class_def)
    # Create class and information for each record type.
    class_for_record_type: dict[ast.Name, ast.ClassDef] = {}
    info_for_record_type: dict[ast.Name, RecordTypeInfo] = {}
    for info in gatherer.record_types:
        class_def_type = make_dataclass_protocol_definition(
            module,
            info.class_name,
            info.type_variables,
            info.fields,
            get_pos_attributes(info.record),
        )
        class_for_record_type[info.record] = class_def_type
        info_for_record_type[info.record] = info
        module.body.insert(get_insert_point_for_class(module), class_def_type)

    _Transform(
        module,
        class_for_record,
        info_for_record,
        class_for_record_type,
        info_for_record_type,
    ).run()
