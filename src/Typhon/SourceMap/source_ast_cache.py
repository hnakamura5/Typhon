import ast

from ..Driver.debugging import debug_verbose_print
from ..Grammar.typhon_ast import get_pos_attributes_if_exists
from .datatype import Pos, Range, RangeIntervalTree


class SourceAstCache:
    def __init__(
        self,
        module: ast.Module,
        source_code: str,
        source_file: str,
    ):
        self.module = module
        self.source_code = source_code
        self.source_file = source_file
        self.source_code_lines = source_code.splitlines()
        self.node_interval_tree = RangeIntervalTree[ast.AST]()
        self.stmt_interval_tree = RangeIntervalTree[ast.stmt]()
        self.expr_interval_tree = RangeIntervalTree[ast.expr]()
        self._setup_interval_trees()

    def _setup_interval_trees(self) -> None:
        for node in ast.walk(self.module):
            pos = get_pos_attributes_if_exists(node)
            if pos is None:
                continue
            node_range = Range.from_pos_attr_may_not_end(pos)
            debug_verbose_print(
                lambda: (
                    f"Adding to source AST interval tree: in {self.source_file}\n"
                    f"    range={node_range}\n"
                    f"    {ast.dump(node)}\n"
                    f"    text={node_range.of_string(self.source_code)}"
                )
            )
            self.node_interval_tree.add(node_range, node)
            if isinstance(node, ast.stmt):
                self.stmt_interval_tree.add(node_range, node)
            if isinstance(node, ast.expr):
                self.expr_interval_tree.add(node_range, node)

    def _pos_to_node[T: ast.AST](
        self,
        pos: Pos,
        interval_tree: RangeIntervalTree[T],
    ) -> T | None:
        nodes = interval_tree.at(pos)
        if not nodes:
            return None
        _, node = min(
            nodes,
            key=lambda entry: (
                entry[0].end.line - entry[0].start.line,
                entry[0].end.column - entry[0].start.column,
            ),
        )
        return node

    def _range_to_node[T: ast.AST](
        self,
        range: Range,
        interval_tree: RangeIntervalTree[T],
    ) -> T | None:
        nodes = interval_tree.minimal_containers(range)
        debug_verbose_print(
            lambda: f"Source AST minimal containers for range {range}: {nodes}"
        )
        if len(nodes) != 1:
            return None
        _, node = nodes[0]
        return node

    def source_pos_to_node(
        self,
        pos: Pos,
    ) -> ast.AST | None:
        return self._pos_to_node(pos, self.node_interval_tree)

    def source_range_to_node(
        self,
        range: Range,
    ) -> ast.AST | None:
        return self._range_to_node(range, self.node_interval_tree)

    def source_pos_to_stmt(
        self,
        pos: Pos,
    ) -> ast.stmt | None:
        return self._pos_to_node(pos, self.stmt_interval_tree)

    def source_range_to_stmt(
        self,
        range: Range,
    ) -> ast.stmt | None:
        return self._range_to_node(range, self.stmt_interval_tree)

    def source_pos_to_expr(
        self,
        pos: Pos,
    ) -> ast.expr | None:
        return self._pos_to_node(pos, self.expr_interval_tree)

    def source_range_to_expr(
        self,
        range: Range,
    ) -> ast.expr | None:
        return self._range_to_node(range, self.expr_interval_tree)

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
