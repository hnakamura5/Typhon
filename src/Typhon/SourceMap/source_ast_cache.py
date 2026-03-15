import ast
from typing import cast

from ..Driver.debugging import debug_verbose_print
from ..Grammar.typhon_ast import get_pos_attributes_if_exists, PythonScope
from .datatype import Pos, Range, RangeIntervalTree


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
        self._setup_parent_map()
        self._setup_interval_trees()

    def _setup_parent_map(self) -> None:
        for parent in ast.walk(self.module):
            for child in ast.iter_child_nodes(parent):
                self.parent_map[child] = parent

    def _setup_interval_trees(self) -> None:
        for node in ast.walk(self.module):
            pos = get_pos_attributes_if_exists(node)
            if pos is None:
                continue
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

    def _pos_to_node(
        self,
        pos: Pos,
        filter_node_type: type[ast.AST] | None = None,
    ) -> ast.AST | None:
        nodes = self.node_interval_tree.at(pos)
        if filter_node_type is not None:
            nodes = [(r, n) for r, n in nodes if isinstance(n, filter_node_type)]
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

    def _range_to_node(
        self,
        range: Range,
        filter_node_type: type[ast.AST] | None = None,
    ) -> ast.AST | None:
        def _filter_node(node: ast.AST) -> bool:
            if filter_node_type is None:
                return True
            return isinstance(node, filter_node_type)

        nodes = self.node_interval_tree.minimal_containers(range, _filter_node)
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
        filter_node_type: type[ast.AST] | None = None,
    ) -> ast.AST | None:
        return self._pos_to_node(pos, filter_node_type)

    def source_range_to_node(
        self,
        range: Range,
        filter_node_type: type[ast.AST] | None = None,
    ) -> ast.AST | None:
        return self._range_to_node(range, filter_node_type)

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
        return cast(PythonScope | None, scope)

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
