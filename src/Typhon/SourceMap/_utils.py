import ast
from typing import Callable

from .datatype import Range, RangeInterval, RangeIntervalTree


def index_node_by_line[T](
    index: dict[int, list[RangeInterval[T]]],
    node_range: Range,
    node: T,
) -> None:
    for line in range(node_range.start.line, node_range.end.line + 1):
        if line not in index:
            index[line] = []
        index[line].append((node_range, node))


def line_to_node[T](
    line: int,
    line_index: dict[int, list[RangeInterval[T]]],
    filter_fn: Callable[[T], bool] | None = None,
) -> T | None:
    nodes = line_index.get(line, [])
    if filter_fn is not None:
        nodes = [(r, n) for r, n in nodes if filter_fn(n)]
    return RangeIntervalTree[T].most_specific_node(nodes)


def filter_fn_by_node_type(
    node_type: type[ast.AST] | None,
) -> Callable[[ast.AST], bool] | None:
    if node_type is None:
        return None
    return lambda node: isinstance(node, node_type)
