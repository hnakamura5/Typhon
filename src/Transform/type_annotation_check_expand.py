import ast
from typing import override

from ..Grammar.typhon_ast import (
    is_decl_assign,
    PosAttributes,
    get_pos_attributes,
    get_type_annotation,
    get_annotations_of_declaration_target,
    copy_is_let_var,
)
from ..Grammar.syntax_errors import raise_type_annotation_error
from .visitor import TyphonASTTransformer


def _expand_target_annotation(
    target: ast.expr,
    annotation: ast.expr,
    orig_node: ast.Assign | ast.AnnAssign | ast.For | ast.withitem,
    pos: PosAttributes,
) -> list[ast.AST]:
    result: list[ast.AST] = []
    annotations = get_annotations_of_declaration_target(target, annotation)
    if not annotations:
        return raise_type_annotation_error(
            "Type annotation form error in declaration", **pos
        )
    for target, type_annotation in annotations:
        if not type_annotation:
            return raise_type_annotation_error(
                "Type annotation form error in declaration", **pos
            )
        new_assign = ast.AnnAssign(
            target=target,
            annotation=type_annotation,
            value=None,  # Type annotation only
            simple=1,
            **pos,
        )
        result.append(new_assign)
        copy_is_let_var(orig_node, new_assign)
    return result


class StmtTypeAnnotationCheckExpand(TyphonASTTransformer):
    # Expand type annotations in declaration by decl_star_target.
    # For example,
    #    let (a, b): (int, str) = (1, "")
    # is expanded to
    #    a: int
    #    b: str
    #    let (a, b) = (1, "")

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not is_decl_assign(node):
            return self.generic_visit(node)
        if node.annotation is None:
            return self.generic_visit(node)
        if isinstance(node.target, ast.Name):
            return self.generic_visit(node)
        if node.value is None:
            return [
                *_expand_target_annotation(
                    node.target, node.annotation, node, get_pos_attributes(node)
                ),
            ]
        # Convert value assignment part into simple Assign.
        assign = ast.Assign(
            targets=[node.target],
            value=node.value,
            **get_pos_attributes(node),
        )
        return [
            *_expand_target_annotation(
                node.target, node.annotation, node, get_pos_attributes(node)
            ),
            self.generic_visit(assign),
        ]

    @override
    def visit_For(self, node: ast.For):
        annotation = get_type_annotation(node)
        if annotation is None:
            return self.generic_visit(node)
        return [
            *_expand_target_annotation(
                node.target, annotation, node, get_pos_attributes(node)
            ),
            self.generic_visit(node),
        ]

    @override
    def visit_With(self, node: ast.With):
        annotation_assignments = []
        for item in node.items:
            annotation = get_type_annotation(item)
            if annotation is None or item.optional_vars is None:
                continue
            annotation_assignments.extend(
                _expand_target_annotation(
                    item.optional_vars, annotation, item, get_pos_attributes(node)
                )
            )
        return [
            *annotation_assignments,
            self.generic_visit(node),
        ]


def type_annotation_check_expand(tree: ast.Module):
    StmtTypeAnnotationCheckExpand(tree).run()
