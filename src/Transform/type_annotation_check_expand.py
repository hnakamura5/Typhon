import ast
from typing import override

from ..Grammar.typhon_ast import (
    is_decl_assign,
    PosAttributes,
    get_pos_attributes,
    get_type_annotation,
    get_annotations_of_declaration_target,
    copy_is_let_var,
    clear_type_annotation,
)
from ..Grammar.syntax_errors import raise_type_annotation_error
from .visitor import TyphonASTTransformer, TyphonASTVisitor, flat_append


def _expand_target_annotation(
    target: ast.expr,
    annotation: ast.expr,
    orig_node: ast.Assign | ast.AnnAssign | ast.For | ast.withitem | ast.comprehension,
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


class _StmtTypeAnnotationCheckExpand(TyphonASTTransformer):
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
        clear_type_annotation(node)
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
            clear_type_annotation(item)
        return [
            *annotation_assignments,
            self.generic_visit(node),
        ]


class _GatherComprehensionAnnotations(TyphonASTVisitor):
    parent_to_clause_annotated: dict[ast.stmt, list[ast.comprehension]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.parent_to_clause_annotated = {}

    @override
    def visit_comprehension(self, node: ast.comprehension):
        self.generic_visit(node)
        annotation = get_type_annotation(node)
        if annotation is not None:
            parent_stmt = self.parent_stmts[-1]
            # TODO If let support?
            self.parent_to_clause_annotated.setdefault(parent_stmt, []).append(node)


class _ComprehensionTypeAnnotationExpand(TyphonASTTransformer):
    # Expand type annotations in comprehension by decl_star_target.
    # For example,
    #    sq = [for (let x: int in range(10)) yield x * x]
    # is expanded to
    #    x: int
    #    sq = [for (let x in range(10)) yield x * x]
    def __init__(
        self,
        module: ast.Module,
        parent_to_clause_annotated: dict[ast.stmt, list[ast.comprehension]],
    ):
        super().__init__(module)
        self.parent_to_clause_annotated = parent_to_clause_annotated

    def visit(self, node: ast.AST):
        if isinstance(node, ast.stmt) and node in self.parent_to_clause_annotated:
            result: list[ast.AST] = []
            for clause in self.parent_to_clause_annotated[node]:
                annotation = get_type_annotation(clause)
                if annotation is None:
                    continue
                result.extend(
                    _expand_target_annotation(
                        clause.target, annotation, clause, get_pos_attributes(node)
                    )
                )
                clear_type_annotation(clause)
            super_result = super().visit(node)
            flat_append(result, super_result)
            return result
        return super().visit(node)


class _SingleNameTypeAnnotationGather(TyphonASTVisitor):
    single_name_annots: list[tuple[ast.stmt, ast.Name, ast.expr]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.single_name_annots = []

    def visit_Name(self, node: ast.Name):
        annotation = get_type_annotation(node)
        print(
            "visit_Name:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
        )  # [HN] For debug.
        if annotation is not None:
            parent_stmt = self.parent_stmts[-1]
            self.single_name_annots.append((parent_stmt, node, annotation))
            clear_type_annotation(node)
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred):
        annotation = get_type_annotation(node)
        print(
            "visit_Starred:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
        )  # [HN] For debug.
        if annotation is not None:
            if isinstance(node.value, ast.Name):
                self.single_name_annots.append(
                    (self.parent_stmts[-1], node.value, annotation)
                )
                clear_type_annotation(node)
        self.generic_visit(node)

    def visit_PossiblyAnnotatedPattern(self, node: ast.MatchAs | ast.MatchStar):
        annotation = get_type_annotation(node)
        print(
            "visit_PossiblyAnnotatedPattern:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
        )  # [HN] For debug.
        if annotation is not None:
            if node.name is not None:
                self.single_name_annots.append(
                    (
                        self.parent_stmts[-1],
                        ast.Name(
                            id=node.name, ctx=ast.Store(), **get_pos_attributes(node)
                        ),
                        annotation,
                    )
                )
            clear_type_annotation(node)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs):
        self.visit_PossiblyAnnotatedPattern(node)

    def visit_MatchStar(self, node: ast.MatchStar):
        self.visit_PossiblyAnnotatedPattern(node)


class _SingleNameTypeAnnotationExpand(TyphonASTTransformer):
    # Expand type annotations of single name inside star target.
    # For example,
    #    let (x: int, y: int) = (1, 2)
    # is expanded to
    #    x: int
    #    y: int
    #    let x, y = 1, 2
    def __init__(
        self,
        module: ast.Module,
        parent_stmt_to_names: dict[ast.stmt, list[tuple[ast.Name, ast.expr]]],
    ):
        super().__init__(module)
        self.parent_stmt_to_names = parent_stmt_to_names

    def visit(self, node: ast.AST):
        if isinstance(node, ast.stmt) and node in self.parent_stmt_to_names:
            result: list[ast.AST] = []
            for name, annotation in self.parent_stmt_to_names[node]:
                if annotation is None:
                    continue
                pos = get_pos_attributes(name)
                new_assign = ast.AnnAssign(
                    target=ast.Name(id=name.id, ctx=ast.Store(), **pos),
                    annotation=annotation,
                    value=None,  # Type annotation only
                    simple=1,
                    **pos,
                )
                result.append(new_assign)
            super_result = super().visit(node)
            flat_append(result, super_result)
            return result
        return super().visit(node)


def type_annotation_check_expand(module: ast.Module):
    _StmtTypeAnnotationCheckExpand(module).run()
    # Expand comprehension clause annotations.
    gather = _GatherComprehensionAnnotations(module)
    gather.run()
    if gather.parent_to_clause_annotated:
        _ComprehensionTypeAnnotationExpand(
            module, gather.parent_to_clause_annotated
        ).run()
    # Expand single name annotations inside star target.
    single_name_gather = _SingleNameTypeAnnotationGather(module)
    single_name_gather.run()
    if single_name_gather.single_name_annots:
        parent_stmt_to_names: dict[ast.stmt, list[tuple[ast.Name, ast.expr]]] = {}
        for parent_stmt, name, annotation in single_name_gather.single_name_annots:
            parent_stmt_to_names.setdefault(parent_stmt, []).append((name, annotation))
        _SingleNameTypeAnnotationExpand(module, parent_stmt_to_names).run()
