import ast
from typing import override, Callable
from contextlib import contextmanager

from .utils.imports import add_import_for_final, get_final, get_final_of_type
from ..Grammar.typhon_ast import (
    DeclarableStmt,
    is_decl_assign,
    PosAttributes,
    get_pos_attributes,
    get_type_annotation,
    get_annotations_of_declaration_target,
    copy_is_let_var,
    clear_type_annotation,
    is_let,
    is_var,
)
from ..Grammar.syntax_errors import (
    raise_type_annotation_error,
    handle_syntax_error,
    TyphonTransformSyntaxError,
)
from .visitor import TyphonASTTransformer, TyphonASTVisitor, flat_append
from ..Driver.debugging import debug_print, debug_verbose_print


def _expand_target_annotation(
    module: ast.Module,
    target: ast.expr,
    annotation: ast.expr | None,
    orig_node: ast.Assign | ast.AnnAssign | ast.For | ast.withitem | ast.comprehension,
    use_final: Callable[[], None],
    pos: PosAttributes,
) -> list[ast.stmt]:
    try:
        result: list[ast.stmt] = []
        annotations = get_annotations_of_declaration_target(target, annotation)
        if not annotations:
            raise_type_annotation_error(
                "Type annotation form error in declaration", **pos
            )
            return []  # TODO: This may cause further errors.
        for target, type_annotation in annotations:
            if is_let(orig_node):
                # 'let' requires type annotation to be 'Final[...]'.
                type_annotation = get_final_of_type(type_expr=type_annotation, **pos)
                use_final()
            if not type_annotation:
                continue
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
    except TyphonTransformSyntaxError as e:
        handle_syntax_error(module, e)
        return []


class _StmtTypeAnnotationCheckExpand(TyphonASTTransformer):
    # Expand type annotations in declaration by decl_star_target.
    # For example,
    #    let (a, b): (int, str) = (1, "")
    # is expanded to
    #    a: int
    #    b: str
    #    let (a, b) = (1, "")
    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.use_final = False

    def _set_use_final(self):
        self.use_final = True

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not is_decl_assign(node):
            return self.generic_visit(node)
        # Keep the simple case as is.
        self.generic_visit(node)
        if is_let(node):
            node.annotation = get_final_of_type(
                type_expr=node.annotation, **get_pos_attributes(node)
            )
            self._set_use_final()
        return node

    @override
    def visit_For(self, node: ast.For):
        annotation = get_type_annotation(node)
        clear_type_annotation(node)
        annotations = _expand_target_annotation(
            self.module,
            node.target,
            annotation,
            node,
            self._set_use_final,
            get_pos_attributes(node),
        )
        self.generic_visit(node)
        node.body = [*annotations, *node.body]
        return node
        # return [
        #     *_expand_target_annotation(
        #         self.module, node.target, annotation, node, get_pos_attributes(node)
        #     ),
        #     self.generic_visit(node),
        # ]

    @override
    def visit_With(self, node: ast.With):
        annotation_assignments: list[ast.stmt] = []
        for item in node.items:
            annotation = get_type_annotation(item)
            if item.optional_vars is None:
                continue
            annotation_assignments.extend(
                _expand_target_annotation(
                    self.module,
                    item.optional_vars,
                    annotation,
                    item,
                    self._set_use_final,
                    get_pos_attributes(node),
                )
            )
            clear_type_annotation(item)
        self.generic_visit(node)
        node.body = [*annotation_assignments, *node.body]
        return node
        # return [
        #     *annotation_assignments,
        #     self.generic_visit(node),
        # ]

    @override
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.name is not None:
            final_ann_assign = ast.AnnAssign(
                target=ast.Name(
                    id=node.name,
                    ctx=ast.Store(),
                    **get_pos_attributes(node),
                ),
                annotation=get_final(ctx=ast.Load(), **get_pos_attributes(node)),
                value=None,  # Type annotation only
                simple=1,
                **get_pos_attributes(node),
            )
            self._set_use_final()
            self.generic_visit(node)
            node.body = [final_ann_assign, *node.body]
            return node
        return self.generic_visit(node)


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
        self.use_final = False

    def _set_use_final(self):
        self.use_final = True

    def visit(self, node: ast.AST):
        if isinstance(node, ast.stmt) and node in self.parent_to_clause_annotated:
            result: list[ast.AST] = []
            for clause in self.parent_to_clause_annotated[node]:
                annotation = get_type_annotation(clause)
                if annotation is None:
                    continue
                result.extend(
                    _expand_target_annotation(
                        self.module,
                        clause.target,
                        annotation,
                        clause,
                        self._set_use_final,
                        get_pos_attributes(node),
                    )
                )
                clear_type_annotation(clause)
            super_result = super().visit(node)
            flat_append(result, super_result)
            return result
        return super().visit(node)


class _PatternAndAssignTypeAnnotationGather(TyphonASTVisitor):
    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.annot_in_cases: dict[
            ast.match_case | ast.Assign, list[tuple[ast.Name, ast.expr | None, bool]]
        ] = {}
        self.decl_contexts: list[ast.match_case | ast.Assign] = []
        self.current_is_const: list[bool] = []
        self.is_class_pattern = False

    @contextmanager
    def decl_context(self, node: ast.match_case | ast.Assign, is_const: bool):
        self.decl_contexts.append(node)
        self.current_is_const.append(is_const)
        yield
        self.current_is_const.pop()
        self.decl_contexts.pop()

    @contextmanager
    def class_pattern_context(self, is_class_pattern: bool = True):
        old_value = self.is_class_pattern
        self.is_class_pattern = is_class_pattern
        yield
        self.is_class_pattern = old_value

    def visit_Assign(self, node: ast.Assign):
        debug_verbose_print(
            f"Visiting type_annot_gather Assign: {ast.dump(node)} is_decl_assign={is_decl_assign(node)}"
        )
        if not is_decl_assign(node):
            return self.generic_visit(node)
        with self.decl_context(node, is_let(node)):
            for target in node.targets:
                self.visit(target)
        self.visit(node.value)
        debug_verbose_print(
            f"Finished type_annot_gather Assign: {ast.dump(node)} is_decl_assign={is_decl_assign(node)}"
        )

    def visit_match_case(self, node: ast.match_case):
        debug_verbose_print(
            f"Visiting type_annot_gather match_case: {ast.dump(node)} is_const={not is_var(node.pattern)}"
        )
        with self.decl_context(node, not is_var(node.pattern)):  # Default is const
            self.visit(node.pattern)
        if node.guard:
            self.visit(node.guard)
        for stmt in node.body:
            self.visit(stmt)
        debug_verbose_print(
            f"Finished type_annot_gather match_case: {ast.dump(node)} is_const={is_let(node.pattern)}"
        )

    def visit_MatchClass(self, node: ast.MatchClass):
        debug_verbose_print(
            f"Visiting type_annot_gather MatchClass: {ast.dump(node)} is_class_pattern=True"
        )
        with self.class_pattern_context(True):
            self.visit(node.cls)  # cls is not a declaration pattern
        for pattern in node.patterns:
            self.visit(pattern)
        for kwd_pattern in node.kwd_patterns:
            self.visit(kwd_pattern)
        return node

    def visit_Name(self, node: ast.Name):
        annotation = get_type_annotation(node)
        debug_verbose_print(
            "visit_Name type_annot_gather:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
            "is_const:",
            self.current_is_const and self.current_is_const[-1],
            "is_class_pattern:",
            self.is_class_pattern,
            "decl_contexts:",
            self.decl_contexts,
        )
        if self.decl_contexts and not self.is_class_pattern:
            if self.current_is_const:
                if annotation is not None or self.current_is_const[-1]:
                    self.annot_in_cases.setdefault(self.decl_contexts[-1], []).append(
                        (node, annotation, self.current_is_const[-1])
                    )
            clear_type_annotation(node)
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred):
        annotation = get_type_annotation(node)
        debug_verbose_print(
            "visit_Starred type_annot_gather:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
            "is_const:",
            self.current_is_const and self.current_is_const[-1],
            "is_class_pattern:",
            self.is_class_pattern,
            "decl_contexts:",
            self.decl_contexts,
        )
        if self.decl_contexts and not self.is_class_pattern:
            if isinstance(node.value, ast.Name):
                if self.current_is_const:
                    if annotation is not None or self.current_is_const[-1]:
                        self.annot_in_cases.setdefault(
                            self.decl_contexts[-1], []
                        ).append((node.value, annotation, self.current_is_const[-1]))
                clear_type_annotation(node)
        self.generic_visit(node)

    def visit_PossiblyAnnotatedPattern(self, node: ast.MatchAs | ast.MatchStar):
        annotation = get_type_annotation(node)
        debug_verbose_print(
            "visit_PossiblyAnnotatedPattern type_annot_gather:",
            ast.dump(node),
            "annot:",
            ast.dump(annotation) if annotation else "None",
            "is_const:",
            self.current_is_const[-1],
            "is_class_pattern:",
            self.is_class_pattern,
            "decl_contexts:",
            self.decl_contexts,
        )
        if self.decl_contexts and not self.is_class_pattern:
            if node.name is not None:
                if self.current_is_const:
                    if annotation is not None or self.current_is_const[-1]:
                        self.annot_in_cases.setdefault(
                            self.decl_contexts[-1], []
                        ).append(
                            (
                                ast.Name(
                                    id=node.name,
                                    ctx=ast.Store(),
                                    **get_pos_attributes(node),
                                ),
                                annotation,
                                self.current_is_const[-1],
                            )
                        )
            clear_type_annotation(node)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs):
        self.visit_PossiblyAnnotatedPattern(node)

    def visit_MatchStar(self, node: ast.MatchStar):
        self.visit_PossiblyAnnotatedPattern(node)


class _PatternTypeAnnotationExpand(TyphonASTTransformer):
    # Expand type annotations in match case patterns.
    # For example,
    #    match x:
    #        case (a: int, b: str):
    # is expanded to
    #    match x:
    #        case (a, b):
    #            a: int
    #            b: str
    def __init__(
        self,
        module: ast.Module,
        decl_to_names: dict[
            ast.match_case | ast.Assign, list[tuple[ast.Name, ast.expr | None, bool]]
        ],
    ):
        super().__init__(module)
        self.decl_to_names = decl_to_names
        self.use_final = False

    def visit_Assign(self, node: ast.Assign):
        result: list[ast.stmt] = []
        if node in self.decl_to_names:
            pos = get_pos_attributes(node)
            if len(node.targets) == 1:
                # Keep the simple case as is.
                name, annotation, is_const = self.decl_to_names[node][0]
                if is_const:
                    annotation = get_final_of_type(type_expr=annotation, **pos)
                    self.use_final = True
                if annotation:
                    return ast.AnnAssign(
                        target=name,
                        annotation=annotation,
                        value=node.value,
                        simple=1,
                        **pos,
                    )
            for name, annotation, is_const in self.decl_to_names[node]:
                name = ast.Name(id=name.id, ctx=ast.Store(), **get_pos_attributes(name))
                if is_const:
                    annotation = get_final_of_type(type_expr=annotation, **pos)
                    self.use_final = True
                elif annotation is None:
                    continue  # Or error?
                annot_for_name = ast.AnnAssign(
                    target=name,
                    annotation=annotation,
                    value=None,  # Type annotation only
                    simple=1,
                    **pos,
                )
                result.append(annot_for_name)
        self.generic_visit(node)
        return [node, *result]

    def visit_match_case(self, node: ast.match_case):
        result: list[ast.stmt] = []
        if node in self.decl_to_names:
            debug_verbose_print(
                f"Expanding pattern annotations in match_case: {ast.dump(node)}"
            )
            for name, annotation, is_const in self.decl_to_names[node]:
                pos = get_pos_attributes(node)
                name = ast.Name(id=name.id, ctx=ast.Store(), **get_pos_attributes(name))
                debug_verbose_print(
                    f"  name: {ast.dump(name)}, annotation: {ast.dump(annotation) if annotation else 'None'}, is_const: {is_const}"
                )
                if is_const:
                    annotation = get_final_of_type(type_expr=annotation, **pos)
                    self.use_final = True
                elif annotation is None:
                    continue  # Or error?
                new_assign = ast.AnnAssign(
                    target=name,
                    annotation=annotation,
                    value=None,  # Type annotation only
                    simple=1,
                    **pos,
                )
                result.append(new_assign)
        self.generic_visit(node)
        node.body = [*result, *node.body]
        return node


def type_annotation_check_expand(module: ast.Module):
    expander = _StmtTypeAnnotationCheckExpand(module)
    expander.run()
    use_final = expander.use_final
    # Expand comprehension clause annotations.
    gather = _GatherComprehensionAnnotations(module)
    gather.run()
    if gather.parent_to_clause_annotated:
        expander = _ComprehensionTypeAnnotationExpand(
            module, gather.parent_to_clause_annotated
        )
        expander.run()
        use_final |= expander.use_final
    # Expand single name annotations inside star target.
    case_gather = _PatternAndAssignTypeAnnotationGather(module)
    case_gather.run()
    if case_gather.annot_in_cases:
        expander = _PatternTypeAnnotationExpand(module, case_gather.annot_in_cases)
        expander.run()
        use_final |= expander.use_final
    if use_final:
        add_import_for_final(module)
