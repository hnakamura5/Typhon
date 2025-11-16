from typing import Protocol
from .datatype import Range
import ast


class SourceMap(Protocol):
    source_file: str
    source_code: str

    def unparsed_range_to_origin(
        self,
        range_unparsed: Range,
    ) -> Range | None: ...

    def unparsed_range_to_source_code(
        self,
        range_unparsed: Range,
    ) -> str | None: ...

    def origin_range_to_unparsed(
        self,
        range_origin: Range,
    ) -> Range | None: ...

    def origin_node_to_unparsed_range(
        self,
        origin_node: ast.AST,
    ) -> Range | None: ...
