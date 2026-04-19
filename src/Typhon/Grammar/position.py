from __future__ import annotations

import ast
from dataclasses import dataclass
import keyword
from re import A
from tokenize import TokenInfo
from typing import TypedDict, Tuple

from ..Driver.debugging import debug_verbose_print


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


def name_from_anchor_token(
    token: TokenInfo | PosNode, ctx: ast.expr_context = ast.Load()
) -> ast.Name:
    if isinstance(token, TokenInfo):
        return ast.Name(
            id=token.string,
            lineno=token.start[0],
            col_offset=token.start[1],
            end_lineno=token.end[0],
            end_col_offset=token.end[1],
            ctx=ctx,
        )
    else:  # PosNode
        pos = get_pos_attributes(token)
        return ast.Name(
            id="",  # Placeholder, the actual name doesn't matter for position tracking
            lineno=pos["lineno"],
            col_offset=pos["col_offset"],
            end_lineno=pos["end_lineno"],
            end_col_offset=pos["end_col_offset"],
            ctx=ctx,
        )


_COMPLETION_TRIGGER_ANCHOR = "_typh_completion_trigger_anchor"


def set_completion_trigger_anchor[T: ast.AST](node: T, anchor: ast.Name | None) -> T:
    setattr(node, _COMPLETION_TRIGGER_ANCHOR, anchor)
    if anchor is not None:
        debug_verbose_print(
            lambda: (
                f"set_completion_trigger_anchor: anchor: {ast.dump(anchor) if anchor else None}, node: {ast.dump(node)}, name pos={get_pos_attributes(anchor) if anchor else None}"
            )
        )
    return node


def get_completion_trigger_anchor(node: ast.AST) -> ast.Name | None:
    return getattr(node, _COMPLETION_TRIGGER_ANCHOR, None)


def clear_completion_trigger_anchor(node: ast.AST):
    if hasattr(node, _COMPLETION_TRIGGER_ANCHOR):
        delattr(node, _COMPLETION_TRIGGER_ANCHOR)


@dataclass
class ExprCommaAnchors:
    commas: list[ast.Name]
    trailing_comma: ast.Name | None = None


_EXPR_COMMA_ANCHORS = "_typh_expr_comma_anchors"


def set_expr_comma_anchors[T: ast.expr](node: T, anchors: ExprCommaAnchors | None) -> T:
    setattr(node, _EXPR_COMMA_ANCHORS, anchors)
    return node


def get_expr_comma_anchors(node: ast.expr) -> ExprCommaAnchors | None:
    return getattr(node, _EXPR_COMMA_ANCHORS, None)


def clear_expr_comma_anchors(node: ast.expr):
    if hasattr(node, _EXPR_COMMA_ANCHORS):
        delattr(node, _EXPR_COMMA_ANCHORS)


_CLASS_BASE_COMMA_ANCHORS = "_typh_class_base_comma_anchors"
_CLASS_TYPE_PARAM_COMMA_ANCHORS = "_typh_class_type_param_comma_anchors"


def set_class_base_comma_anchors(
    node: ast.ClassDef, anchors: ExprCommaAnchors | None
) -> ast.ClassDef:
    setattr(node, _CLASS_BASE_COMMA_ANCHORS, anchors)
    return node


def get_class_base_comma_anchors(node: ast.ClassDef) -> ExprCommaAnchors | None:
    return getattr(node, _CLASS_BASE_COMMA_ANCHORS, None)


def clear_class_base_comma_anchors(node: ast.ClassDef):
    if hasattr(node, _CLASS_BASE_COMMA_ANCHORS):
        delattr(node, _CLASS_BASE_COMMA_ANCHORS)


def set_class_type_param_comma_anchors(
    node: ast.ClassDef, anchors: ExprCommaAnchors | None
) -> ast.ClassDef:
    setattr(node, _CLASS_TYPE_PARAM_COMMA_ANCHORS, anchors)
    return node


def get_class_type_param_comma_anchors(
    node: ast.ClassDef,
) -> ExprCommaAnchors | None:
    return getattr(node, _CLASS_TYPE_PARAM_COMMA_ANCHORS, None)


def clear_class_type_param_comma_anchors(node: ast.ClassDef):
    if hasattr(node, _CLASS_TYPE_PARAM_COMMA_ANCHORS):
        delattr(node, _CLASS_TYPE_PARAM_COMMA_ANCHORS)


_FUNCTION_ARG_COMMA_ANCHORS = "_typh_function_arg_comma_anchors"
_FUNCTION_TYPE_PARAM_COMMA_ANCHORS = "_typh_function_type_param_comma_anchors"


def set_function_arg_comma_anchors[T: ast.FunctionDef | ast.AsyncFunctionDef](
    node: T,
    anchors: ExprCommaAnchors | None,
) -> T:
    setattr(node, _FUNCTION_ARG_COMMA_ANCHORS, anchors)
    return node


def get_function_arg_comma_anchors(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ExprCommaAnchors | None:
    return getattr(node, _FUNCTION_ARG_COMMA_ANCHORS, None)


def clear_function_arg_comma_anchors(node: ast.FunctionDef | ast.AsyncFunctionDef):
    if hasattr(node, _FUNCTION_ARG_COMMA_ANCHORS):
        delattr(node, _FUNCTION_ARG_COMMA_ANCHORS)


def set_function_type_param_comma_anchors[T: ast.FunctionDef | ast.AsyncFunctionDef](
    node: T,
    anchors: ExprCommaAnchors | None,
) -> T:
    setattr(node, _FUNCTION_TYPE_PARAM_COMMA_ANCHORS, anchors)
    return node


def get_function_type_param_comma_anchors(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ExprCommaAnchors | None:
    return getattr(node, _FUNCTION_TYPE_PARAM_COMMA_ANCHORS, None)


def clear_function_type_param_comma_anchors(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
):
    if hasattr(node, _FUNCTION_TYPE_PARAM_COMMA_ANCHORS):
        delattr(node, _FUNCTION_TYPE_PARAM_COMMA_ANCHORS)


_RETURN_TYPE_ANNOTATION_ANCHOR = "_typh_return_type_annotation_anchor"


def set_return_type_annotation_anchor(
    node: ast.FunctionDef | ast.AsyncFunctionDef, anchor: ast.Name | None
):
    setattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR, anchor)


def get_return_type_annotation_anchor(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.Name | None:
    return getattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR, None)


def clear_return_type_annotation_anchor(node: ast.FunctionDef | ast.AsyncFunctionDef):
    if hasattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR):
        delattr(node, _RETURN_TYPE_ANNOTATION_ANCHOR)


# Represents 'else' and 'finally' blocks
@dataclass
class TrailingBlock:
    keyword: TokenInfo
    body: list[ast.stmt]


@dataclass
class BlockStmtAnchors:
    # Sequent of tokens beggining of the statements. (e.g. 'async' and 'def')
    begin_token_anchors: list[ast.Name]
    open_paren_anchor: ast.Name | None
    close_paren_anchor: ast.Name | None
    open_brace_anchor: ast.Name | None
    close_brace_anchor: ast.Name | None
    # for else in if-else, for-else, while-else and so on.
    else_brace_open_anchor: ast.Name | None
    else_brace_close_anchor: ast.Name | None
    # finally block
    finally_open_anchor: ast.Name | None
    finally_close_anchor: ast.Name | None
    inner_separator_anchors: list[ast.Name]

    @staticmethod
    def make(
        *,
        keywords: list[TokenInfo],
        parens: tuple[TokenInfo, TokenInfo] | None = None,
        braces: tuple[TokenInfo, TokenInfo] | None = None,
        else_block: TrailingBlock | None = None,
        finally_block: TrailingBlock | None = None,
    ) -> BlockStmtAnchors:
        inner_separator_anchors: list[ast.Name] = []
        else_braces = None
        finally_braces = None
        if else_block is not None:
            else_braces = get_block_braces(else_block.body)
            inner_separator_anchors.append(name_from_anchor_token(else_block.keyword))
        if finally_block is not None:
            finally_braces = get_block_braces(finally_block.body)
            inner_separator_anchors.append(
                name_from_anchor_token(finally_block.keyword)
            )
        return BlockStmtAnchors(
            begin_token_anchors=[name_from_anchor_token(k) for k in keywords],
            open_paren_anchor=name_from_anchor_token(parens[0]) if parens else None,
            close_paren_anchor=name_from_anchor_token(parens[1]) if parens else None,
            open_brace_anchor=name_from_anchor_token(braces[0]) if braces else None,
            close_brace_anchor=name_from_anchor_token(braces[1]) if braces else None,
            else_brace_open_anchor=name_from_anchor_token(else_braces[0])
            if else_braces
            else None,
            else_brace_close_anchor=name_from_anchor_token(else_braces[1])
            if else_braces
            else None,
            finally_open_anchor=name_from_anchor_token(finally_braces[0])
            if finally_braces
            else None,
            finally_close_anchor=name_from_anchor_token(finally_braces[1])
            if finally_braces
            else None,
            inner_separator_anchors=inner_separator_anchors,
        )


@dataclass
class InlineStmtAnchors:
    begin_token_anchors: list[ast.Name]
    appendix_anchor: ast.Name  # `else` for let-else


_STMT_OPEN_PAREN_ANCHOR = "_typh_stmt_open_paren_anchor"


def set_block_stmt_anchors[T: PosNode](node: T, anchor: BlockStmtAnchors | None) -> T:
    setattr(node, _STMT_OPEN_PAREN_ANCHOR, anchor)
    return node


def get_block_stmt_anchors(node: PosNode) -> BlockStmtAnchors | None:
    return getattr(node, _STMT_OPEN_PAREN_ANCHOR, None)


def clear_block_stmt_anchors(node: PosNode):
    if hasattr(node, _STMT_OPEN_PAREN_ANCHOR):
        delattr(node, _STMT_OPEN_PAREN_ANCHOR)


_INLINE_STMT_ANCHOR = "_typh_inline_stmt_anchor"


def set_inline_stmt_anchor[T: PosNode](node: T, anchor: InlineStmtAnchors | None) -> T:
    setattr(node, _INLINE_STMT_ANCHOR, anchor)
    return node


def get_inline_stmt_anchor(node: PosNode) -> InlineStmtAnchors | None:
    return getattr(node, _INLINE_STMT_ANCHOR, None)


def clear_inline_stmt_anchor(node: PosNode):
    if hasattr(node, _INLINE_STMT_ANCHOR):
        delattr(node, _INLINE_STMT_ANCHOR)


_BLOCK_BRACES = "_typh_block_braces"


def get_block_braces(body: list[ast.stmt]) -> tuple[TokenInfo, TokenInfo] | None:
    if not body:
        return None
    return getattr(body[0], _BLOCK_BRACES, None)


def set_block_braces(
    body: list[ast.stmt], open_brace: TokenInfo, close_brace: TokenInfo
):
    assert body, "Cannot set block braces on empty body"
    setattr(body[0], _BLOCK_BRACES, (open_brace, close_brace))


def clear_block_braces(body: list[ast.stmt]):
    if body:
        if hasattr(body[0], _BLOCK_BRACES):
            delattr(body[0], _BLOCK_BRACES)
