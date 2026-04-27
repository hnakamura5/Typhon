import ast
from contextlib import contextmanager
import traceback
from typing import Callable

from ..Driver.debugging import debug_verbose_print
from ..Grammar.position import (
    PosNode,
    get_block_stmt_anchors,
    get_completion_trigger_anchor,
    get_prefix_format_anchor,
    get_expr_format_anchors,
    get_pos_attributes_if_exists,
    get_return_type_annotation_anchor,
)
from ..Grammar.typhon_ast import (
    get_defined_name,
    get_function_literal_def,
    get_import_from_names,
    get_match_class_keyword_names,
    get_lossless_token_info,
    is_function_literal,
    is_function_type,
    PythonScope,
    set_prefix_format_anchor_token,
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
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.ExceptHandler,
                ast.MatchAs,
                ast.alias,
                ast.Attribute,
                ast.arg,
                ast.keyword,
                ast.FormattedValue,
                ast.TypeVar,
                ast.TypeVarTuple,
                ast.ParamSpec,
            ),
        ):
            if defined_name := get_defined_name(node):
                self._visit_anchor(defined_name)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if return_type_anchor := get_return_type_annotation_anchor(node):
                self._visit_anchor(return_type_anchor)

        if isinstance(node, ast.ImportFrom):
            for import_name in get_import_from_names(node):
                self._visit_anchor(import_name)

        if isinstance(node, ast.MatchClass):
            for keyword_name in get_match_class_keyword_names(node) or []:
                self._visit_anchor(keyword_name)

        # if completion_anchor := get_completion_trigger_anchor(node):
        #     self._visit_anchor(completion_anchor)

        if prefix_anchor := get_prefix_format_anchor(node):
            self._visit_anchor(prefix_anchor)

        if comma_anchors := get_expr_format_anchors(node):
            for comma_anchor in comma_anchors.commas:
                self._visit_anchor(comma_anchor)
            if comma_anchors.trailing_comma is not None:
                self._visit_anchor(comma_anchors.trailing_comma)
            if comma_anchors.surround_open is not None:
                self._visit_anchor(comma_anchors.surround_open)
            if comma_anchors.surround_close is not None:
                self._visit_anchor(comma_anchors.surround_close)
            for keyword_anchor in comma_anchors.keywords or []:
                self._visit_anchor(keyword_anchor)

        if isinstance(node, PosNode):
            if block_anchors := get_block_stmt_anchors(node):
                for anchor in block_anchors.keywords:
                    self._visit_anchor(anchor)
                if block_anchors.open_type_param_bracket_anchor is not None:
                    self._visit_anchor(block_anchors.open_type_param_bracket_anchor)
                if block_anchors.close_type_param_bracket_anchor is not None:
                    self._visit_anchor(block_anchors.close_type_param_bracket_anchor)
                for comma_anchor in block_anchors.type_param_comma_anchors:
                    self._visit_anchor(comma_anchor)
                if block_anchors.type_param_trailing_comma_anchor is not None:
                    self._visit_anchor(block_anchors.type_param_trailing_comma_anchor)
                if block_anchors.open_paren_anchor is not None:
                    self._visit_anchor(block_anchors.open_paren_anchor)
                if block_anchors.close_paren_anchor is not None:
                    self._visit_anchor(block_anchors.close_paren_anchor)
                for comma_anchor in block_anchors.param_comma_anchors:
                    self._visit_anchor(comma_anchor)
                if block_anchors.param_trailing_comma_anchor is not None:
                    self._visit_anchor(block_anchors.param_trailing_comma_anchor)
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
        *,
        format_mode: bool = False,
    ):
        self.module = module
        self.source_code = source_code
        self.source_file_path = source_file_path
        self.source_code_lines = source_code.splitlines()
        self.parent_map: dict[ast.AST, ast.AST | None] = {module: None}
        self.node_interval_tree = RangeIntervalTree[ast.AST]()
        self.nodes_by_line: dict[int, list[tuple[Range, ast.AST]]] = {}
        self._set_stmt_separator_prefix_anchors()
        self._setup_interval_trees()
        self._format_mode = format_mode

    def _set_stmt_separator_prefix_anchors(self) -> None:
        tokens = get_lossless_token_info(self.module) or []
        semicolon_tokens = [tok for tok in tokens if tok.string == ";"]
        if not semicolon_tokens:
            return

        parents: list[ast.AST] = list(ast.walk(self.module))
        for node in parents:
            if isinstance(node, ast.Name) and is_function_literal(node):
                if func_def := get_function_literal_def(node):
                    parents.append(func_def)

        for parent in parents:
            for _, value in ast.iter_fields(parent):
                if not (
                    isinstance(value, list)
                    and len(value) > 1
                    and all(isinstance(stmt, ast.stmt) for stmt in value)
                ):
                    continue
                stmt_list = value
                for prev_stmt, next_stmt in zip(stmt_list, stmt_list[1:]):
                    if get_prefix_format_anchor(next_stmt) is not None:
                        continue
                    prev_pos = get_pos_attributes_if_exists(prev_stmt)
                    next_pos = get_pos_attributes_if_exists(next_stmt)
                    if prev_pos is None or next_pos is None:
                        continue
                    prev_end = (
                        prev_pos["end_lineno"] or prev_pos["lineno"],
                        prev_pos["end_col_offset"] or prev_pos["col_offset"],
                    )
                    next_start = (next_pos["lineno"], next_pos["col_offset"])
                    if prev_end >= next_start:
                        continue
                    for token in semicolon_tokens:
                        if prev_end <= token.start and token.end <= next_start:
                            set_prefix_format_anchor_token(next_stmt, token)
                            break

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
                f"    {ast.dump(node, include_attributes=True)}\n"
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
