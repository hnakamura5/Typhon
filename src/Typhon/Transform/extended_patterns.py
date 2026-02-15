import ast
from dataclasses import dataclass
from typing import Protocol, Iterable, Final
from ..Grammar.typhon_ast import (
    RecordLiteral,
    copy_is_let_var,
    get_record_literal_fields,
    get_record_type_fields,
    get_pos_attributes,
    pos_attribute_to_range,
    get_empty_pos_attributes,
    PosAttributes,
    set_is_var,
    is_record_literal,
    is_record_type,
    is_attributes_pattern,
    is_pattern_tuple,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from ._utils.imports import (
    get_insert_point_for_class,
)
from ._utils.make_class import (
    make_protocol_definition,
)


@dataclass
class AttributePatternFieldInfo:
    name: ast.Name
    annotation: ast.expr


@dataclass
class AttributePatternInfo:
    class_name: str
    pattern: ast.MatchClass
    record: ast.Name
    type_variables: list[str]
    fields: list[AttributePatternFieldInfo]


class _GatherRecords(TyphonASTVisitor):
    record_patterns: list[AttributePatternInfo]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.record_patterns = []

    def visit_MatchClass(self, node: ast.MatchClass):
        if isinstance(node.cls, ast.Name) and is_attributes_pattern(node.cls):
            record_cls = node.cls
            type_vars: list[str] = []
            fields: list[AttributePatternFieldInfo] = []
            # Gather the member names from keyword patterns.
            for kwd_name in node.kwd_attrs:
                type_var = self.new_typevar_name(kwd_name)
                type_vars.append(type_var)
                fields.append(
                    AttributePatternFieldInfo(
                        name=ast.Name(
                            id=kwd_name,
                            ctx=ast.Load(),
                            **get_pos_attributes(node.cls),
                        ),
                        annotation=ast.Name(
                            id=type_var, ctx=ast.Load(), **get_pos_attributes(node.cls)
                        ),
                    )
                )
            self.record_patterns.append(
                AttributePatternInfo(
                    self.new_class_name(""),
                    node,
                    record_cls,
                    type_vars,
                    fields,
                )
            )
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    def __init__(
        self,
        module: ast.Module,
        class_for_record_pattern: dict[ast.Name, ast.ClassDef],
        info_for_record_pattern: dict[ast.Name, AttributePatternInfo],
    ):
        super().__init__(module)
        self.class_for_record_pattern = class_for_record_pattern
        self.info_for_record_pattern = info_for_record_pattern

    def visit_Name(self, node: ast.Name):
        if node in self.class_for_record_pattern:
            class_def = self.class_for_record_pattern[node]
            info = self.info_for_record_pattern[node]
            return ast.Name(
                id=class_def.name, ctx=ast.Load(), **get_pos_attributes(node)
            )
        return self.generic_visit(node)

    # Convert tuple pattern
    def visit_MatchSequence(self, node: ast.MatchSequence):
        if is_pattern_tuple(node):
            pos = get_pos_attributes(node)
            return copy_is_let_var(
                node,
                ast.MatchClass(
                    cls=ast.Name(id="tuple", ctx=ast.Load(), **pos),
                    patterns=[
                        ast.MatchSequence(node.patterns, **pos_attribute_to_range(pos))
                    ],
                    kwd_attrs=[],
                    kwd_patterns=[],
                    **pos_attribute_to_range(pos),
                ),
            )
        return self.generic_visit(node)


def extended_protocol(module: ast.Module):
    gatherer = _GatherRecords(module)
    gatherer.run()
    # Create class and information for each record pattern.
    class_for_record_pattern: dict[ast.Name, ast.ClassDef] = {}
    info_for_record_pattern: dict[ast.Name, AttributePatternInfo] = {}
    for info in gatherer.record_patterns:
        class_def_type = make_protocol_definition(
            module,
            info.class_name,
            info.type_variables,
            info.fields,
            get_pos_attributes(info.record),
        )
        class_for_record_pattern[info.record] = class_def_type
        info_for_record_pattern[info.record] = info
        module.body.insert(get_insert_point_for_class(module), class_def_type)
    _Transform(
        module,
        class_for_record_pattern,
        info_for_record_pattern,
    ).run()
