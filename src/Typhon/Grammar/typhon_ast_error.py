import ast
from typing import Unpack, cast
from tokenize import TokenInfo
from .typhon_ast import (
    PosAttributes,
    unpack_pos_default,
    get_pos_attributes,
    PosNode,
    make_for_let_pattern,
    make_function_def,
    make_class_def,
    get_invalid_name,
    unpack_pos_tuple,
)
from ..Driver.debugging import debug_print
from .parser_helper import Parser
from .syntax_errors import set_syntax_error


_ERROR_NODE = "_typh_error_node"


def set_error_node[T: ast.AST](node: T, errors: list[SyntaxError]) -> T:
    setattr(node, _ERROR_NODE, errors)
    return node


def set_error_list[T: ast.AST](nodes: list[T], errors: list[SyntaxError]) -> list[T]:
    setattr(nodes, _ERROR_NODE, errors)
    return nodes


def add_error_node[T: ast.AST](node: T, errors: list[SyntaxError]) -> T:
    return set_error_node(node, get_error_node(node) + errors)


def add_error_list[T: ast.AST](nodes: list[T], errors: list[SyntaxError]) -> list[T]:
    return set_error_list(nodes, get_error_list(nodes) + errors)


def get_error_node(node: ast.AST) -> list[SyntaxError]:
    return getattr(node, _ERROR_NODE, [])


def get_error_list[T: ast.AST](nodes: list[T]) -> list[SyntaxError]:
    return getattr(nodes, _ERROR_NODE, [])


def clear_error_node(node: ast.AST) -> None:
    if hasattr(node, _ERROR_NODE):
        delattr(node, _ERROR_NODE)


def clear_error_list(nodes: list[ast.AST]) -> None:
    if hasattr(nodes, _ERROR_NODE):
        delattr(nodes, _ERROR_NODE)


class ErrorPositionHolder(PosAttributes):
    pass


def maybe_invalid_block(
    parser: Parser,
    open_brace: TokenInfo | None,
    close_brace: TokenInfo | None,
    body: list[ast.stmt],
) -> list[ast.stmt]:
    if open_brace is None:
        if body:
            stmt = body[0]
            lineno, col_offset, _, _ = unpack_pos_default(get_pos_attributes(stmt))
            error_open = parser.build_syntax_error(
                "expected '{'",
                (lineno, col_offset),
                (lineno, col_offset + 1),
            )
            add_error_list(body, [error_open])
    if close_brace is None:
        if body:
            stmt = body[-1]
            _, _, lineno, col_offset = unpack_pos_default(get_pos_attributes(stmt))
            error_close = parser.build_syntax_error(
                "expected '}'",
                (lineno, col_offset),
                (lineno, col_offset + 1),
            )
            add_error_list(body, [error_close])
    return body


def maybe_invalid_braces[T: PosNode](
    parser: Parser,
    open_brace: TokenInfo | None,
    close_brace: TokenInfo | None,
    node: T,
    *,
    open_anchor: PosNode | TokenInfo | None = None,
) -> T:
    lineno, col_offset, end_lineno, end_col_offset = unpack_pos_default(
        get_pos_attributes(node)
    )
    if open_anchor:
        _, _, lineno, col_offset = unpack_pos_default(get_pos_attributes(open_anchor))
    if open_brace is None:
        error_open = parser.build_syntax_error(
            "expected '{'",
            (lineno, col_offset),
            (lineno, col_offset + 1),
        )
        add_error_node(node, [error_open])

    if close_brace is None:
        error_close = parser.build_syntax_error(
            "expected '}'",
            (end_lineno, end_col_offset),
            (end_lineno, end_col_offset + 1),
        )
        add_error_node(node, [error_close])
    return node


def _pos_of_anchor(
    anchor: PosNode | TokenInfo,
) -> tuple[tuple[int, int], tuple[int, int]]:
    if isinstance(anchor, TokenInfo):
        return anchor.end, _next_col(anchor.end)
    else:  # PosNode
        _, _, e_lineno, e_col = unpack_pos_default(get_pos_attributes(anchor))
        start_loc = (e_lineno, e_col)
        end_loc = _next_col(start_loc)
        return start_loc, end_loc


def _next_col(pos: tuple[int, int]) -> tuple[int, int]:
    return pos[0], pos[1] + 1


def maybe_invalid_stmt[T: PosNode](
    parser: Parser,
    open_paren: TokenInfo | None,
    close_paren: TokenInfo | None,
    *,
    node: T,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    message: str | None = None,
    message_anchor: PosNode | TokenInfo | None = None,
) -> T:
    lineno, col_offset, end_lineno, end_col_offset = unpack_pos_default(
        get_pos_attributes(node)
    )
    if message is not None:
        error = parser.build_syntax_error(
            message,
            (lineno, col_offset),
            (end_lineno, end_col_offset),
        )
        add_error_node(node, [error])
    if open_paren is None:
        start_loc, end_loc = _pos_of_anchor(open_anchor)
        debug_print(
            f"open paren missing: {start_loc} to {end_loc} open anchor: {open_anchor}"
        )
        error = parser.build_syntax_error("expected '('", start_loc, end_loc)
        add_error_node(node, [error])
    if close_paren is None:
        start_loc, end_loc = _pos_of_anchor(close_anchor)
        debug_print(
            f"close paren missing: {start_loc} to {end_loc} close anchor: {close_anchor}"
        )
        error = parser.build_syntax_error("expected ')'", start_loc, end_loc)
        add_error_node(node, [error])
    return node


def recover_invalid_try(
    parser: Parser,
    message: str,
    node: ast.Try,
) -> ast.Try:
    lineno, col_offset, end_lineno, end_col_offset = unpack_pos_default(
        get_pos_attributes(node)
    )
    error = parser.build_syntax_error(
        message,
        (lineno, col_offset),
        (end_lineno, end_col_offset),
    )
    return add_error_node(node, [error])


def recover_invalid_for(
    parser: Parser,
    open_paren: TokenInfo | None,
    close_paren: TokenInfo | None,
    is_async: bool,
    decl_keyword: TokenInfo | None,
    pattern: ast.pattern | None,
    in_keyword: TokenInfo | None,
    expression: ast.expr | None,
    body: list[ast.stmt],
    *,
    open_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.For | ast.AsyncFor:
    current_anchor: tuple[int, int] = _pos_of_anchor(open_anchor)[0]
    errors: list[SyntaxError] = []

    def error_expect(mes: str):
        nonlocal errors
        nonlocal current_anchor
        error = parser.build_expected_error(
            mes,
            current_anchor,
            _next_col(current_anchor),
        )
        errors.append(error)
        current_anchor = _next_col(current_anchor)

    if not open_paren:
        error_expect("'('")
    else:
        current_anchor = open_paren.end
    if not decl_keyword:
        error_expect("'let/var'")
        decl = "let"
    else:
        current_anchor = decl_keyword.end
        decl = decl_keyword.string
    if not pattern:
        error_expect("pattern")
        pattern = ast.MatchAs(name=None)
    else:
        current_anchor = (pattern.end_lineno, pattern.end_col_offset)
    if not in_keyword:
        error_expect("'in'")
    else:
        current_anchor = _pos_of_anchor(in_keyword)[1]
    if not expression:
        error_expect("expression")
        expression = ast.Constant(
            value=Ellipsis,
            lineno=current_anchor[0],
            col_offset=current_anchor[1],
            end_lineno=current_anchor[0],
            end_col_offset=current_anchor[1] + 1,
        )
    else:
        current_anchor = _pos_of_anchor(expression)[1]
    if not close_paren:
        error_expect("')'")
    else:
        current_anchor = close_paren.end
    for_node = make_for_let_pattern(
        parser,
        decl_type=decl,
        pattern=pattern,
        iter=expression,
        body=body,
        orelse=[],
        type_comment=None,
        is_async=is_async,
        **kwargs,
    )
    add_error_node(for_node, errors)
    return for_node


def recover_maybe_invalid_function_def_raw(
    parser: Parser,
    is_async: bool,
    is_static: bool,
    name: TokenInfo | str | None,
    open_paren: TokenInfo | None,
    args: ast.arguments,
    close_paren: TokenInfo | None,
    returns: ast.expr | None,
    body: list[ast.stmt],
    type_comment: str | None,
    type_params: list[ast.type_param],
    *,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    start_pos, end_pos = _pos_of_anchor(open_anchor)
    error: SyntaxError | None = None
    if not name:
        error = parser.build_expected_error("function name", start_pos, end_pos)
    result = maybe_invalid_stmt(
        parser,
        open_paren,
        close_paren,
        node=make_function_def(
            is_async=is_async,
            is_static=is_static,
            name=name or get_invalid_name(),
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            **kwargs,
        ),
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    if error:
        add_error_node(result, [error])
    return result


def recover_maybe_invalid_class_def_raw(
    parser: Parser,
    name: TokenInfo | str | None,
    bases_parens: tuple[
        TokenInfo, tuple[list[ast.expr], list[ast.keyword]], TokenInfo | None
    ]
    | None,
    body: list[ast.stmt],
    decorator_list: list[ast.expr],
    type_params: list[ast.type_param],
    *,
    open_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.ClassDef:
    start_pos, end_pos = _pos_of_anchor(open_anchor)
    open_paren, (bases, keywords), close_paren = bases_parens or (None, ([], []), None)
    close_anchor = (
        bases[-1]
        if bases
        else (
            type_params[-1]
            if type_params
            else (name if isinstance(name, TokenInfo) else open_anchor)
        )
    )
    error: SyntaxError | None = None
    if not name:
        error = parser.build_expected_error("class name", start_pos, end_pos)
    class_def = make_class_def(
        name=name or get_invalid_name(),
        bases=bases,
        keywords=keywords,
        body=body,
        decorator_list=decorator_list,
        type_params=type_params,
        **kwargs,
    )
    if bases:
        maybe_invalid_stmt(
            parser,
            open_paren,
            close_paren,
            node=class_def,
            open_anchor=open_anchor,
            close_anchor=close_anchor,
        )
    if error:
        add_error_node(class_def, [error])
    return class_def


def statement_panic_skip(
    parser: Parser,
    skip: list[TokenInfo],
    sync: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> list[ast.stmt]:
    if sync:
        skip.append(sync)
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    if skip:
        start_loc, _ = _pos_of_anchor(skip[0])
        _, end_loc = _pos_of_anchor(skip[-1])
    # Record the skipped tokens for error recovery
    error = parser.build_skip_tokens_error(skip, start_loc, end_loc)
    result = ast.Pass(**kwargs)  # Error holder
    add_error_node(result, [error])
    return [result]


class _ErrorGather(ast.NodeVisitor):
    errors: list[SyntaxError]

    def __init__(self):
        self.errors = []
        super().__init__()

    def visit(self, node: ast.AST):
        if errors := get_error_node(node):
            self.errors.extend(errors)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                if errors := get_error_list(cast(list[ast.AST], value)):
                    self.errors.extend(errors)
        self.generic_visit(node)


def gather_errors(node: ast.AST):
    gather = _ErrorGather()
    gather.visit(node)
    parse_errors = sorted(gather.errors, key=lambda e: (e.lineno, e.offset))
    set_syntax_error(node, parse_errors)
