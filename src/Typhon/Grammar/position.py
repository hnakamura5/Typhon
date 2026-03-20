from __future__ import annotations

import ast
from tokenize import TokenInfo
from typing import TypedDict, Tuple


# Same as ast module's position attributes
class PosAttributes(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


def unpack_pos_default(pos: PosAttributes) -> Tuple[int, int, int, int]:
    return (
        pos["lineno"],
        pos["col_offset"],
        pos["end_lineno"] or pos["lineno"],
        pos["end_col_offset"] or pos["col_offset"] + 1,
    )


def unpack_pos_tuple(pos: PosAttributes) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    return (
        (pos["lineno"], pos["col_offset"]),
        (
            pos["end_lineno"] or pos["lineno"],
            pos["end_col_offset"] or pos["col_offset"] + 1,
        ),
    )


class PosRange(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int


def pos_attribute_to_range(pos: PosAttributes) -> PosRange:
    result: PosRange = {
        "lineno": pos["lineno"],
        "col_offset": pos["col_offset"],
        "end_lineno": pos["end_lineno"]
        if pos["end_lineno"] is not None
        else pos["lineno"],
        "end_col_offset": pos["end_col_offset"]
        if pos["end_col_offset"] is not None
        else pos["col_offset"],
    }

    return result


PosNode = (
    ast.stmt
    | ast.expr
    | ast.alias
    | ast.arg
    | ast.type_param
    | ast.excepthandler
    | ast.pattern
    | ast.keyword
    | ast.match_case
)


def get_pos_attributes(node: PosNode | TokenInfo) -> PosAttributes:
    if isinstance(node, TokenInfo):
        return PosAttributes(
            lineno=node.start[0],
            col_offset=node.start[1],
            end_lineno=node.end[0],
            end_col_offset=node.end[1],
        )
    return PosAttributes(
        lineno=getattr(node, "lineno", 1),
        col_offset=getattr(node, "col_offset", 0),
        end_lineno=getattr(node, "end_lineno", None),
        end_col_offset=getattr(node, "end_col_offset", None),
    )


def get_pos_attributes_if_exists(node: ast.AST) -> PosAttributes | None:
    if hasattr(node, "lineno") and hasattr(node, "col_offset"):
        return PosAttributes(
            lineno=getattr(node, "lineno"),
            col_offset=getattr(node, "col_offset"),
            end_lineno=getattr(node, "end_lineno", None),
            end_col_offset=getattr(node, "end_col_offset", None),
        )
    return None


def get_lineno_col_offset(node: ast.AST) -> Tuple[int, int]:
    pos = get_pos_attributes_if_exists(node)
    if pos is not None:
        return (pos["lineno"], pos["col_offset"])
    else:
        return (0, 0)


def get_empty_pos_attributes() -> PosAttributes:
    # Python ast position is 1-based for line, 0-based for column
    return PosAttributes(
        lineno=1,
        col_offset=0,
        end_lineno=1,
        end_col_offset=0,
    )
