from typing import Callable, Protocol
from .datatype import Range, Pos
import ast


class SourceMap(Protocol):
    source_file: str
    source_code: str

    def unparsed_node_to_origin_node(
        self,
        unparsed_node: ast.AST,
    ) -> ast.AST | None: ...

    def unparsed_range_to_origin_range(
        self,
        range_unparsed: Range,
    ) -> Range | None: ...

    def unparsed_range_to_source_code(
        self,
        range_unparsed: Range,
    ) -> str | None: ...

    def origin_range_to_unparsed_range(
        self,
        range_origin: Range,
    ) -> Range | None: ...

    def origin_node_to_unparsed_range(
        self,
        origin_node: ast.AST,
    ) -> Range | None: ...

    def origin_pos_to_unparsed_pos(
        self,
        pos_origin: Pos,
        prefer_right: bool = True,
    ) -> Pos | None: ...

    def unparsed_pos_to_origin_pos(
        self,
        pos_unparsed: Pos,
        prefer_right: bool = True,
    ) -> Pos | None: ...

    def origin_pos_to_unparsed_node(
        self,
        pos_origin: Pos,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def origin_pos_to_origin_node(
        self,
        pos_origin: Pos,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def origin_line_to_origin_node(
        self,
        line_origin: int,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def origin_range_to_origin_node(
        self,
        range_origin: Range,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def unparsed_pos_to_origin_node(
        self,
        pos_unparsed: Pos,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def unparsed_line_to_unparsed_node(
        self,
        line_unparsed: int,
        filter_node_type: type[ast.AST] | None = None,
        filter_pred: Callable[[ast.AST], bool] | None = None,
    ) -> ast.AST | None: ...

    def unparsed_code_end_pos(self) -> Pos: ...
