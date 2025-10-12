import ast
from ..Grammar.typhon_ast import (
    RecordLiteral,
    get_record_literal_fields,
    get_pos_attributes,
    pos_attribute_noneless,
    get_empty_pos_attributes,
    PosAttributes,
    set_is_var,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from .utils import (
    add_import_for_dataclass,
    add_import_for_protocol,
    add_import_for_final,
    get_insert_point_for_class,
)
from dataclasses import dataclass


@dataclass
class RecordInfo:
    record: RecordLiteral
    class_name: str
    fields: list[tuple[ast.Name, ast.expr]]
    type_variables: list[str]


class _GatherRecords(TyphonASTVisitor):
    records: list[RecordInfo]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.records = []

    def visit_Name(self, node: RecordLiteral):
        fields = get_record_literal_fields(node)
        if fields is not None:
            type_vars = [self.new_typevar_name(name.id) for name, _ in fields]
            self.records.append(
                RecordInfo(node, self.new_class_name(""), fields, type_vars)
            )
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


def _class_contents_for_fields(info: RecordInfo) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for index, (name, _) in enumerate(info.fields):
        annotation = ast.Name(
            id=info.type_variables[index], ctx=ast.Load(), **get_pos_attributes(name)
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


def _type_vars_for_fields(info: RecordInfo) -> list[ast.type_param]:
    type_params: list[ast.type_param] = []
    for tv in info.type_variables:
        type_params.append(
            ast.TypeVar(
                name=tv, **pos_attribute_noneless(get_pos_attributes(info.record))
            )
        )
    return type_params


def _add_repr_to_dataclass(class_def: ast.ClassDef, info: RecordInfo):
    repr_values: list[ast.expr] = []
    repr_values.append(ast.Constant(value="{|", **get_pos_attributes(info.record)))
    for field_name, _ in info.fields:
        repr_values.append(
            ast.Constant(value=f"{field_name.id}=", **get_pos_attributes(field_name))
        )
        repr_values.append(
            ast.FormattedValue(
                value=ast.Attribute(
                    value=ast.Name(
                        id="self", ctx=ast.Load(), **get_pos_attributes(field_name)
                    ),
                    attr=field_name.id,
                    ctx=ast.Load(),
                    **get_pos_attributes(field_name),
                ),
                conversion=b"r"[0],  # !r conversion
                format_spec=None,
            )
        )
        repr_values.append(ast.Constant(value=", ", **get_pos_attributes(field_name)))
    if len(repr_values) > 1:
        repr_values.pop()  # Remove the last comma
    repr_values.append(ast.Constant(value="|}", **get_pos_attributes(info.record)))
    # __repr__ method return the f-string.
    repr_func_def = ast.FunctionDef(
        name="__repr__",
        args=ast.arguments(),
        body=[
            ast.Return(
                value=ast.JoinedStr(
                    values=repr_values, **get_pos_attributes(info.record)
                ),
                **get_pos_attributes(info.record),
            )
        ],
        **get_pos_attributes(info.record),
    )
    class_def.body.append(repr_func_def)


def _make_dataclass_definition(
    info: RecordInfo,
    dataclass_imported_name: str,
) -> ast.ClassDef:
    result = ast.ClassDef(
        name=info.class_name,
        type_params=_type_vars_for_fields(info),
        bases=[],
        keywords=[],
        body=_class_contents_for_fields(info),
        decorator_list=[
            _dataclass_decorator(
                dataclass_imported_name, repr=False, pos=get_pos_attributes(info.record)
            )
        ],
        **get_pos_attributes(info.record),
    )
    _add_repr_to_dataclass(result, info)
    return result


class _Transform(TyphonASTTransformer):
    def __init__(
        self,
        module: ast.Module,
        class_for_record: dict[ast.Name, ast.ClassDef],
        info_for_record: dict[ast.Name, RecordInfo],
    ):
        super().__init__(module)
        self.class_for_record = class_for_record
        self.info_for_record = info_for_record

    def visit_Name(self, node: ast.Name):
        if node in self.class_for_record:
            class_def = self.class_for_record[node]
            pos = get_pos_attributes(node)
            return ast.Call(
                func=ast.Name(id=class_def.name, ctx=ast.Load(), **pos),
                args=[],
                keywords=[
                    ast.keyword(arg=name.id, value=value, **get_pos_attributes(name))
                    for name, value in self.info_for_record[node].fields
                ],
                **pos,
            )
        return self.generic_visit(node)


# Run before other transformations so that the generated call is visited properly.
def record_to_dataclass(module: ast.Module):
    gatherer = _GatherRecords(module)
    gatherer.run()
    if not gatherer.records:
        return
    dataclass_imported_name = add_import_for_dataclass(module)
    class_for_record: dict[ast.Name, ast.ClassDef] = {}
    info_for_record: dict[ast.Name, RecordInfo] = {}
    insert_point = get_insert_point_for_class(module)
    for info in gatherer.records:
        class_def = _make_dataclass_definition(info, dataclass_imported_name)
        class_for_record[info.record] = class_def
        info_for_record[info.record] = info
        module.body.insert(insert_point, class_def)
        insert_point += 1
    _Transform(module, class_for_record, info_for_record).run()
    print(f"dump module after record_to_dataclass: {ast.dump(module)}")
