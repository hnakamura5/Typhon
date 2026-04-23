import ast
from contextlib import contextmanager
import traceback
from typing import Callable

from ..Driver.debugging import debug_verbose_print
from ..Grammar.position import (
    PosNode,
    get_class_base_comma_anchors,
    get_class_type_param_comma_anchors,
    get_block_stmt_anchors,
    get_completion_trigger_anchor,
    get_expr_comma_anchors,
    get_function_arg_comma_anchors,
    get_function_literal_arg_comma_anchors,
    get_function_type_arg_comma_anchors,
    get_function_type_param_comma_anchors,
    get_inline_stmt_anchor,
    get_pos_attributes_if_exists,
    get_return_type_annotation_anchor,
)
from ..Grammar.typhon_ast import (
    is_function_literal,
    is_function_type,
    PythonScope,
    get_record_literal_fields,
    get_record_type_fields,
    is_internal_fallback_stmt,
)
from ..Transform.visitor import TyphonASTRawVisitor
from .datatype import Pos, Range, RangeIntervalTree
from ._utils import (
    filter_fn_by_node_type,
    index_node_by_line,
    line_to_node,
)


class _SourceAstIndexVisitor(TyphonASTRawVisitor):
    def __init__(
        self,
        on_node: Callable[[ast.AST], None],
        parent_map: dict[ast.AST, ast.AST | None],
    ):
        super().__init__()
        self._on_node = on_node
        self._parent_map = parent_map
        self._visited_node_ids: set[int] = set()
        self._parents: list[ast.AST] = []

    @contextmanager
    def _with_parent(self, parent: ast.AST):
        self._parents.append(parent)
        yield
        self._parents.pop()

    def _visit_anchor(self, anchor: ast.AST) -> None:
        # if isinstance(anchor, ast.Name) and anchor.id == "":
        #     # Placeholder anchors can share source ranges with real expression nodes,
        #     # causing ambiguous range lookup results.
        #     return
        debug_verbose_print(
            lambda: (
                f"Visiting anchor node: {ast.dump(anchor)}\n"
                f"    source range: {Range.from_ast_node(anchor)}\n"
                # f"    call traceback: {traceback.format_stack()}\n"
            )
        )
        self.visit(anchor)

    def _visit_attached_anchor_nodes(self, node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if return_type_anchor := get_return_type_annotation_anchor(node):
                self._visit_anchor(return_type_anchor)
            if function_arg_anchors := get_function_arg_comma_anchors(node):
                for comma_anchor in function_arg_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if function_arg_anchors.trailing_comma is not None:
                    self._visit_anchor(function_arg_anchors.trailing_comma)
            if function_type_param_anchors := get_function_type_param_comma_anchors(
                node
            ):
                for comma_anchor in function_type_param_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if function_type_param_anchors.trailing_comma is not None:
                    self._visit_anchor(function_type_param_anchors.trailing_comma)

        if isinstance(node, ast.ClassDef):
            if class_base_anchors := get_class_base_comma_anchors(node):
                for comma_anchor in class_base_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if class_base_anchors.trailing_comma is not None:
                    self._visit_anchor(class_base_anchors.trailing_comma)
            if class_type_param_anchors := get_class_type_param_comma_anchors(node):
                for comma_anchor in class_type_param_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if class_type_param_anchors.trailing_comma is not None:
                    self._visit_anchor(class_type_param_anchors.trailing_comma)

        if isinstance(node, ast.Name) and is_function_literal(node):
            if function_literal_arg_anchors := get_function_literal_arg_comma_anchors(
                node
            ):
                for comma_anchor in function_literal_arg_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if function_literal_arg_anchors.trailing_comma is not None:
                    self._visit_anchor(function_literal_arg_anchors.trailing_comma)

        if isinstance(node, ast.Name) and is_function_type(node):
            if function_type_arg_anchors := get_function_type_arg_comma_anchors(node):
                for comma_anchor in function_type_arg_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if function_type_arg_anchors.trailing_comma is not None:
                    self._visit_anchor(function_type_arg_anchors.trailing_comma)

        if completion_anchor := get_completion_trigger_anchor(node):
            self._visit_anchor(completion_anchor)

        if isinstance(node, ast.expr):
            if comma_anchors := get_expr_comma_anchors(node):
                for comma_anchor in comma_anchors.commas:
                    self._visit_anchor(comma_anchor)
                if comma_anchors.trailing_comma is not None:
                    self._visit_anchor(comma_anchors.trailing_comma)

        if isinstance(node, PosNode):
            if block_anchors := get_block_stmt_anchors(node):
                for anchor in block_anchors.begin_token_anchors:
                    self._visit_anchor(anchor)
                if block_anchors.open_type_param_bracket_anchor is not None:
                    self._visit_anchor(block_anchors.open_type_param_bracket_anchor)
                if block_anchors.close_type_param_bracket_anchor is not None:
                    self._visit_anchor(block_anchors.close_type_param_bracket_anchor)
                if block_anchors.open_paren_anchor is not None:
                    self._visit_anchor(block_anchors.open_paren_anchor)
                if block_anchors.close_paren_anchor is not None:
                    self._visit_anchor(block_anchors.close_paren_anchor)
                if block_anchors.open_brace_anchor is not None:
                    self._visit_anchor(block_anchors.open_brace_anchor)
                if block_anchors.close_brace_anchor is not None:
                    self._visit_anchor(block_anchors.close_brace_anchor)
                if block_anchors.else_brace_open_anchor is not None:
                    self._visit_anchor(block_anchors.else_brace_open_anchor)
                if block_anchors.else_brace_close_anchor is not None:
                    self._visit_anchor(block_anchors.else_brace_close_anchor)
                if block_anchors.finally_open_anchor is not None:
                    self._visit_anchor(block_anchors.finally_open_anchor)
                if block_anchors.finally_close_anchor is not None:
                    self._visit_anchor(block_anchors.finally_close_anchor)
                for anchor in block_anchors.inner_separator_anchors:
                    self._visit_anchor(anchor)
            if inline_anchors := get_inline_stmt_anchor(node):
                for anchor in inline_anchors.begin_token_anchors:
                    self._visit_anchor(anchor)
                self._visit_anchor(inline_anchors.appendix_anchor)

    def visit_RecordLiteral(self, node: ast.Name):
        for field_name, field_type, field_value in (
            get_record_literal_fields(node) or []
        ):
            self.visit(field_name)
            if field_type is not None:
                self.visit(field_type)
            self.visit(field_value)
        self._visit_attached_anchor_nodes(node)
        return node

    def visit_RecordType(self, node: ast.Name):
        for field_name, field_type in get_record_type_fields(node) or []:
            self.visit(field_name)
            self.visit(field_type)
        self._visit_attached_anchor_nodes(node)
        return node

    def visit(self, node: ast.AST):
        if isinstance(node, ast.stmt) and is_internal_fallback_stmt(node):
            return None
        node_id = id(node)
        if node_id in self._visited_node_ids:
            return None
        self._visited_node_ids.add(node_id)
        if self._parents:
            self._parent_map.setdefault(node, self._parents[-1])
        debug_verbose_print(
            lambda: (
                f"Visiting source_ast_cache node: {ast.dump(node)}\n"
                f"    source range: {Range.from_ast_node(node)}\n"
                f"    parent: {ast.dump(self._parents[-1]) if self._parents else None}"
            )
        )
        self._on_node(node)
        with self._with_parent(node):
            return super().visit(node)

    def generic_visit(self, node: ast.AST):
        super().generic_visit(node)
        self._visit_attached_anchor_nodes(node)


class SourceAstCache:
    def __init__(
        self,
        module: ast.Module,
        source_code: str,
        source_file_path: str,
    ):
        self.module = module
        self.source_code = source_code
        self.source_file_path = source_file_path
        self.source_code_lines = source_code.splitlines()
        self.parent_map: dict[ast.AST, ast.AST | None] = {module: None}
        self.node_interval_tree = RangeIntervalTree[ast.AST]()
        self.nodes_by_line: dict[int, list[tuple[Range, ast.AST]]] = {}
        self._setup_interval_trees()

    def _setup_parent_map(self) -> None:
        _SourceAstIndexVisitor(
            on_node=lambda _node: None,
            parent_map=self.parent_map,
        ).visit(self.module)

    def _setup_interval_trees(self) -> None:
        _SourceAstIndexVisitor(
            on_node=self._index_node_interval,
            parent_map=self.parent_map,
        ).visit(self.module)

    def _index_node_interval(self, node: ast.AST) -> None:
        pos = get_pos_attributes_if_exists(node)
        if pos is None:
            return
        node_range = Range.from_pos_attr_may_not_end(pos)
        debug_verbose_print(
            lambda: (
                f"Adding to source AST interval tree: in {self.source_file_path}\n"
                f"    range={node_range}\n"
                f"    {ast.dump(node)}\n"
                f"    text={node_range.of_string(self.source_code)}"
            )
        )
        self.node_interval_tree.add(node_range, node)
        index_node_by_line(self.nodes_by_line, node_range, node)

    def source_pos_to_node(
        self,
        pos: Pos,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None:
        return self.node_interval_tree.pos_to_node(
            pos,
            filter_fn_by_node_type(filter_node_type, filter_pred),
        )

    def source_range_to_node(
        self,
        range: Range,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None:
        return self.node_interval_tree.range_to_minimal_container_node(
            range,
            filter_fn_by_node_type(filter_node_type, filter_pred),
        )

    def source_line_to_node(
        self,
        line: int,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None:
        return line_to_node(
            line,
            self.nodes_by_line,
            filter_fn_by_node_type(filter_node_type, filter_pred),
        )

    def parent_of(self, node: ast.AST) -> ast.AST | None:
        return self.parent_map.get(node, None)

    def ancestors_of(self, node: ast.AST) -> list[ast.AST]:
        result: list[ast.AST] = []
        current = self.parent_of(node)
        while current is not None:
            result.append(current)
            current = self.parent_of(current)
        return result

    def innermost_enclosing(
        self,
        node: ast.AST | None,
        node_type: type[ast.AST] | tuple[type[ast.AST], ...],
    ) -> ast.AST | None:
        current = node
        while current is not None:
            if isinstance(current, node_type):
                return current
            current = self.parent_of(current)
        return None

    def outermost_enclosing(
        self,
        node: ast.AST | None,
        node_type: type[ast.AST] | tuple[type[ast.AST], ...],
    ) -> ast.AST | None:
        current = node
        enclosing: ast.AST | None = None
        while current is not None:
            if isinstance(current, node_type):
                enclosing = current
            current = self.parent_of(current)
        return enclosing

    def enclosing_scope(self, node: ast.AST | None) -> PythonScope | None:
        scope = self.innermost_enclosing(
            node,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        )
        if not isinstance(scope, PythonScope):
            return None
        return scope

    def source_range_to_source_code(
        self,
        range: Range,
    ) -> str:
        return range.of_string(self.source_code)

    def source_code_end_pos(self) -> Pos:
        if self.source_code_lines:
            return Pos(
                line=len(self.source_code_lines) - 1,
                column=len(self.source_code_lines[-1]),
            )
        return Pos(line=0, column=0)
