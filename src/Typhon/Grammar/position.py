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


_PREFIX_FORMAT_ANCHOR = "_typh_prefix_format_anchor"


def set_prefix_format_anchor[T: ast.AST](node: T, anchor: ast.Name | None) -> T:
    setattr(node, _PREFIX_FORMAT_ANCHOR, anchor)
    return node


def get_prefix_format_anchor(node: ast.AST) -> ast.Name | None:
    return getattr(node, _PREFIX_FORMAT_ANCHOR, None)


def clear_prefix_format_anchor(node: ast.AST):
    if hasattr(node, _PREFIX_FORMAT_ANCHOR):
        delattr(node, _PREFIX_FORMAT_ANCHOR)


@dataclass
class ExprFormatAnchors:
    commas: list[ast.Name]
    trailing_comma: ast.Name | None = None
    keywords: list[ast.Name] | None = None
    surround_open: ast.Name | None = None
    surround_close: ast.Name | None = None

    @staticmethod
    def make(
        *,
        commas: list[TokenInfo] | None = None,
        trailing_comma: TokenInfo | None = None,
        keywords: list[TokenInfo] | None = None,
        surround_open: TokenInfo | None = None,
        surround_close: TokenInfo | None = None,
    ) -> ExprFormatAnchors:
        comma_anchors = (
            [name_from_anchor_token(c) for c in commas] if commas is not None else []
        )
        trailing_comma_anchor = (
            name_from_anchor_token(trailing_comma)
            if trailing_comma is not None
            else None
        )
        keyword_anchors = (
            [name_from_anchor_token(k) for k in keywords]
            if keywords is not None
            else None
        )
        surround_open_anchor = (
            name_from_anchor_token(surround_open) if surround_open is not None else None
        )
        surround_close_anchor = (
            name_from_anchor_token(surround_close)
            if surround_close is not None
            else None
        )
        return ExprFormatAnchors(
            commas=comma_anchors,
            trailing_comma=trailing_comma_anchor,
            keywords=keyword_anchors,
            surround_open=surround_open_anchor,
            surround_close=surround_close_anchor,
        )


_EXPR_COMMA_ANCHORS = "_typh_expr_comma_anchors"


def set_expr_format_anchors[T: ast.AST](
    node: T, anchors: ExprFormatAnchors | None
) -> T:
    setattr(node, _EXPR_COMMA_ANCHORS, anchors)
    return node


def get_expr_format_anchors(node: ast.AST) -> ExprFormatAnchors | None:
    return getattr(node, _EXPR_COMMA_ANCHORS, None)


def clear_expr_format_anchors(node: ast.expr):
    if hasattr(node, _EXPR_COMMA_ANCHORS):
        delattr(node, _EXPR_COMMA_ANCHORS)


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
    keywords: list[ast.Name]
    open_type_param_bracket_anchor: ast.Name | None
    close_type_param_bracket_anchor: ast.Name | None
    type_param_comma_anchors: list[ast.Name]
    type_param_trailing_comma_anchor: ast.Name | None
    open_paren_anchor: ast.Name | None
    close_paren_anchor: ast.Name | None
    param_comma_anchors: list[ast.Name]
    param_trailing_comma_anchor: ast.Name | None
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
        type_param_brackets: tuple[TokenInfo, TokenInfo] | None = None,
        type_param_commas: list[TokenInfo] | None = None,
        type_param_trailing_comma: TokenInfo | None = None,
        parens: tuple[TokenInfo, TokenInfo] | None = None,
        param_commas: list[TokenInfo] | None = None,
        param_trailing_comma: TokenInfo | None = None,
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
            keywords=[name_from_anchor_token(k) for k in keywords],
            open_type_param_bracket_anchor=(
                name_from_anchor_token(type_param_brackets[0])
                if type_param_brackets
                else None
            ),
            close_type_param_bracket_anchor=(
                name_from_anchor_token(type_param_brackets[1])
                if type_param_brackets
                else None
            ),
            type_param_comma_anchors=(
                [name_from_anchor_token(c) for c in type_param_commas]
                if type_param_commas is not None
                else []
            ),
            type_param_trailing_comma_anchor=(
                name_from_anchor_token(type_param_trailing_comma)
                if type_param_trailing_comma is not None
                else None
            ),
            open_paren_anchor=name_from_anchor_token(parens[0]) if parens else None,
            close_paren_anchor=name_from_anchor_token(parens[1]) if parens else None,
            param_comma_anchors=(
                [name_from_anchor_token(c) for c in param_commas]
                if param_commas is not None
                else []
            ),
            param_trailing_comma_anchor=(
                name_from_anchor_token(param_trailing_comma)
                if param_trailing_comma is not None
                else None
            ),
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


_BLOCK_STMT_ANCHOR = "_typh_block_stmt_anchor"


def set_block_stmt_anchors[T: PosNode](node: T, anchor: BlockStmtAnchors | None) -> T:
    setattr(node, _BLOCK_STMT_ANCHOR, anchor)
    return node


def get_block_stmt_anchors(node: PosNode) -> BlockStmtAnchors | None:
    return getattr(node, _BLOCK_STMT_ANCHOR, None)


def clear_block_stmt_anchors(node: PosNode):
    if hasattr(node, _BLOCK_STMT_ANCHOR):
        delattr(node, _BLOCK_STMT_ANCHOR)


# Temporary storage of block braces.
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


# Temporary storages of comment anchors in parser.
_ARG_FOLLOWING_COMMA_TOKEN = "_typh_arg_following_comma_token"
_ARGS_POSONLY_SLASH_COMMA_TOKEN = "_typh_args_posonly_slash_comma_token"
_ARGS_BARE_STAR_COMMA_TOKEN = "_typh_args_bare_star_comma_token"


def set_arg_following_comma_token[T: ast.arg | ast.type_param](
    arg: T,
    comma: TokenInfo | None,
) -> T:
    setattr(arg, _ARG_FOLLOWING_COMMA_TOKEN, comma)
    return arg


def get_arg_following_comma_token(arg: ast.arg | ast.type_param) -> TokenInfo | None:
    return getattr(arg, _ARG_FOLLOWING_COMMA_TOKEN, None)


def set_arguments_posonly_slash_comma_token(
    args: ast.arguments,
    comma: TokenInfo | None,
) -> ast.arguments:
    setattr(args, _ARGS_POSONLY_SLASH_COMMA_TOKEN, comma)
    return args


def get_arguments_posonly_slash_comma_token(
    args: ast.arguments,
) -> TokenInfo | None:
    return getattr(args, _ARGS_POSONLY_SLASH_COMMA_TOKEN, None)


def set_arguments_bare_star_comma_token(
    args: ast.arguments,
    comma: TokenInfo | None,
) -> ast.arguments:
    setattr(args, _ARGS_BARE_STAR_COMMA_TOKEN, comma)
    return args


def get_arguments_bare_star_comma_token(
    args: ast.arguments,
) -> TokenInfo | None:
    return getattr(args, _ARGS_BARE_STAR_COMMA_TOKEN, None)


def get_function_argument_comma_tokens(
    args: ast.arguments,
) -> tuple[list[TokenInfo], TokenInfo | None] | None:
    following_tokens: list[TokenInfo | None] = []

    for arg in args.posonlyargs:
        following_tokens.append(get_arg_following_comma_token(arg))
    if args.posonlyargs:
        following_tokens.append(get_arguments_posonly_slash_comma_token(args))

    for arg in args.args:
        following_tokens.append(get_arg_following_comma_token(arg))

    if args.vararg is not None:
        following_tokens.append(get_arg_following_comma_token(args.vararg))
    elif args.kwonlyargs:
        following_tokens.append(get_arguments_bare_star_comma_token(args))

    for arg in args.kwonlyargs:
        following_tokens.append(get_arg_following_comma_token(arg))

    if args.kwarg is not None:
        following_tokens.append(get_arg_following_comma_token(args.kwarg))

    return get_inner_and_trailing_comma_tokens(following_tokens)


def get_inner_and_trailing_comma_tokens(
    tokens: list[TokenInfo | None],
) -> tuple[list[TokenInfo], TokenInfo | None] | None:
    if not tokens:
        return ([], None)
    inter: list[TokenInfo] = []
    for token in tokens[:-1]:
        assert token is not None, "Missing comma token for argument"
        inter.append(token)
    trailling = tokens[-1]
    return (inter, trailling)
