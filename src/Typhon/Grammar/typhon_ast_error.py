import ast
import copy
from dataclasses import dataclass
from typing import Unpack, cast
from tokenize import TokenInfo
from .position import (
    BlockStmtAnchors,
    PosAttributes,
    TrailingBlock,
    get_empty_pos_attributes,
    pos_attribute_to_range,
    set_block_stmt_anchors,
    unpack_pos_default,
    get_pos_attributes,
    PosNode,
    unpack_pos_tuple,
    get_block_braces,
    set_block_braces,
    get_function_argument_comma_tokens,
)
from .typhon_ast import (
    CallArgs,
    ImportDotNames,
    assign_as_declaration,
    make_arguments,
    make_if_let,
    make_match_case,
    make_for_let_pattern,
    make_function_def,
    make_while_let,
    make_class_def,
    set_control_comprehension_def,
    get_invalid_name,
    set_completion_trigger_anchor_token,
)
from ..Driver.debugging import debug_print, debug_verbose_print
from .parser_helper import Parser
from .syntax_errors import set_syntax_error, add_error_node, get_error_node
from ..Transform.visitor import TyphonASTRawVisitor


def _empty_args() -> ast.arguments:
    return ast.arguments(
        posonlyargs=[],
        args=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[],
        vararg=None,
        kwarg=None,
    )


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
            error_open = parser.build_expected_error(
                "'{'",
                (lineno, col_offset),
                (lineno, col_offset + 1),
            )
            add_error_node(stmt, [error_open])
    if close_brace is None:
        if body:
            stmt = body[-1]
            _, _, lineno, col_offset = unpack_pos_default(get_pos_attributes(stmt))
            error_close = parser.build_expected_error(
                "'}'",
                (lineno, col_offset),
                (lineno, col_offset + 1),
            )
            add_error_node(stmt, [error_close])
    if open_brace and close_brace:
        set_block_braces(body, open_brace, close_brace)
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
        error_open = parser.build_expected_error(
            "'{'",
            (lineno, col_offset),
            (lineno, col_offset + 1),
        )
        add_error_node(node, [error_open])

    if close_brace is None:
        error_close = parser.build_expected_error(
            "'}'",
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


def _set_define_block_stmt_anchors(
    node: PosNode,
    *,
    begin_tokens: list[TokenInfo | None] | None,
    type_param_brackets: tuple[TokenInfo, TokenInfo] | None,
    open_paren: TokenInfo | None,
    close_paren: TokenInfo | None,
    arg_param_commas: list[TokenInfo] | None = None,
    arg_trailing_comma: TokenInfo | None = None,
    type_param_commas: list[TokenInfo] | None = None,
    type_params_trailing_comma: TokenInfo | None = None,
    body: list[ast.stmt] | None,
) -> None:
    brace_anchors = get_block_braces(body) if body else None
    anchors = BlockStmtAnchors.make(
        keywords=[tok for tok in begin_tokens if tok] if begin_tokens else [],
        type_param_brackets=type_param_brackets,
        type_param_commas=type_param_commas if type_param_commas else [],
        type_param_trailing_comma=type_params_trailing_comma,
        parens=(open_paren, close_paren)
        if open_paren is not None and close_paren is not None
        else None,
        param_commas=arg_param_commas if arg_param_commas else [],
        param_trailing_comma=arg_trailing_comma,
        braces=brace_anchors,
        else_block=None,
        finally_block=None,
    )
    set_block_stmt_anchors(node, anchors)


def maybe_invalid_stmt[T: PosNode](
    parser: Parser,
    open_paren: TokenInfo | None,
    close_paren: TokenInfo | None,
    *,
    node: T,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    begin_tokens: list[TokenInfo | None] | None = None,
    message: str | None = None,
    # body and else_block are for taking brace anchors to attach comments.
    body: list[ast.stmt] | None = None,
    else_block: TrailingBlock | None = None,
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
    if open_paren is None:  # Missing open paren
        start_loc, end_loc = _pos_of_anchor(open_anchor)
        debug_print(
            lambda: (
                f"open paren missing: {start_loc} to {end_loc} open anchor: {open_anchor}"
            )
        )
        error = parser.build_expected_error("'('", start_loc, end_loc)
        add_error_node(node, [error])
    if close_paren is None:  # Missing close paren
        start_loc, end_loc = _pos_of_anchor(close_anchor)
        debug_print(
            lambda: (
                f"close paren missing: {start_loc} to {end_loc} close anchor: {close_anchor}"
            )
        )
        error = parser.build_expected_error("')'", start_loc, end_loc)
        add_error_node(node, [error])
    if open_paren and close_paren:
        brace_anchors = get_block_braces(body) if body else None
        set_block_stmt_anchors(
            node,
            BlockStmtAnchors.make(
                keywords=[tok for tok in begin_tokens if tok] if begin_tokens else [],
                parens=(open_paren, close_paren),
                braces=brace_anchors,
                else_block=else_block,
                finally_block=None,
            ),
        )
    return node


def maybe_invalid_close_paren[T: PosNode](
    parser: Parser,
    close_paren: TokenInfo | None,
    *,
    node: T,
    close_anchor: PosNode | TokenInfo,
) -> T:
    if close_paren is None:
        start_loc, end_loc = _pos_of_anchor(close_anchor)
        debug_print(lambda: f"close paren missing: {start_loc} to {end_loc}")
        error = parser.build_expected_error("')'", start_loc, end_loc)
        add_error_node(node, [error])
    return node


def _set_control_comp_stmt_anchors_or_invalid_stmt(
    node: PosNode,
    *,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    missing_parens_is_error: bool = True,  # For try comp, missing paren is not an error.
) -> None:
    open_paren, close_paren = parens
    if not missing_parens_is_error and open_paren is None and close_paren is None:
        set_block_stmt_anchors(
            node,
            BlockStmtAnchors.make(
                keywords=[tok for tok in keyword_tokens if tok]
                if keyword_tokens
                else [],
            ),
        )
        return
    maybe_invalid_stmt(
        parser,
        open_paren,
        close_paren,
        node=node,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
        begin_tokens=keyword_tokens,
    )


def make_with_comp(
    is_async: bool,
    items: list[ast.withitem],
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__with_control"
    with_stmt = ast.With(
        items=items,
        body=[ast.Return(value=body, **get_pos_attributes(body))],
        **kwargs,
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        with_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    func_def = make_function_def(
        is_async=is_async,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[with_stmt],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


_EXCEPT_COMP = "_typh_is_try_comp_except"


# Temporal information holder in parser.
@dataclass
class TryCompExceptInfo:
    name: str | None
    ex_type: ast.expr | None
    body: ast.expr
    keyword_tokens: list[TokenInfo | None]
    parens: tuple[TokenInfo | None, TokenInfo | None]
    parser: Parser
    open_anchor: PosNode | TokenInfo
    close_anchor: PosNode | TokenInfo
    report_missing_parens: bool


def set_try_comp_except(node: ast.Name, info: TryCompExceptInfo):
    setattr(node, _EXCEPT_COMP, info)


def get_try_comp_except(node: ast.Name) -> TryCompExceptInfo:
    return getattr(node, _EXCEPT_COMP)


def clear_try_comp_except(node: ast.Name):
    if hasattr(node, _EXCEPT_COMP):
        delattr(node, _EXCEPT_COMP)


def make_try_comp_except(
    name: str | None,
    ex_type: ast.expr | None,
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    report_missing_parens: bool,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id=name or "", ctx=ast.Load(), **kwargs)
    set_try_comp_except(
        result,
        TryCompExceptInfo(
            name=name,
            ex_type=ex_type,
            body=body,
            keyword_tokens=keyword_tokens,
            parens=parens,
            parser=parser,
            open_anchor=open_anchor,
            close_anchor=close_anchor,
            report_missing_parens=report_missing_parens,
        ),
    )
    return result


def make_try_comp(
    body: ast.expr,
    handlers: list[ast.Name],
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__try_comp"
    if handlers:
        handler_blocks: list[ast.ExceptHandler] = []
        for handler in handlers:
            info = get_try_comp_except(handler)
            except_handler = ast.ExceptHandler(
                type=info.ex_type,
                name=info.name,
                body=[
                    ast.Return(
                        value=info.body,
                        **get_pos_attributes(handler),
                    )
                ],
                **get_pos_attributes(handler),
            )
            _set_control_comp_stmt_anchors_or_invalid_stmt(
                except_handler,
                keyword_tokens=info.keyword_tokens,
                parens=info.parens,
                parser=info.parser,
                open_anchor=info.open_anchor,
                close_anchor=info.close_anchor,
                missing_parens_is_error=info.report_missing_parens,
            )
            handler_blocks.append(except_handler)
            clear_try_comp_except(handler)
    else:
        handler_blocks = [
            ast.ExceptHandler(
                type=None,
                name=None,
                body=[
                    ast.Return(
                        value=ast.Constant(value=None, **get_pos_attributes(body)),
                        **get_pos_attributes(body),
                    )
                ],
                **get_pos_attributes(body),
            )
        ]
    try_stmt = ast.Try(
        body=[ast.Return(value=body, **get_pos_attributes(body))],
        handlers=handler_blocks,
        orelse=[],
        finalbody=[],
        **get_pos_attributes(body),
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        try_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
        missing_parens_is_error=False,
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[try_stmt],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


_CASE_COMP = "_typh_is_case_comp_case"


# Temporal information holder in parser.
@dataclass
class CaseCompCaseInfo:
    pattern: ast.pattern
    guard: ast.expr | None
    body: ast.expr
    keyword_tokens: list[TokenInfo | None]
    parens: tuple[TokenInfo | None, TokenInfo | None]
    parser: Parser
    open_anchor: PosNode | TokenInfo
    close_anchor: PosNode | TokenInfo
    report_missing_parens: bool


def set_case_comp_case(
    node: ast.Name,
    pattern: ast.pattern,
    guard: ast.expr | None,
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    report_missing_parens: bool,
):
    setattr(
        node,
        _CASE_COMP,
        CaseCompCaseInfo(
            pattern=pattern,
            guard=guard,
            body=body,
            keyword_tokens=keyword_tokens,
            parens=parens,
            parser=parser,
            open_anchor=open_anchor,
            close_anchor=close_anchor,
            report_missing_parens=report_missing_parens,
        ),
    )


def get_case_comp_case(
    node: ast.Name,
) -> CaseCompCaseInfo:
    return getattr(node, _CASE_COMP)


def clear_case_comp_case(node: ast.Name):
    if hasattr(node, _CASE_COMP):
        delattr(node, _CASE_COMP)


def make_match_comp_case(
    pattern: ast.pattern,
    guard: ast.expr | None,
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    report_missing_parens: bool,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id="", ctx=ast.Load(), **kwargs)
    set_case_comp_case(
        result,
        pattern,
        guard,
        body,
        keyword_tokens,
        parens,
        parser,
        open_anchor,
        close_anchor,
        report_missing_parens,
    )
    return result


def make_match_comp(
    subject: ast.expr,
    cases: list[ast.Name],
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__match_comp"
    case_nodes: list[ast.match_case] = []
    for case in cases:
        info = get_case_comp_case(case)
        case_node = make_match_case(
            pattern=info.pattern,
            guard=info.guard,
            body=[
                ast.Return(
                    value=info.body,
                    **get_pos_attributes(case),
                )
            ],
            **get_pos_attributes(case),
        )
        _set_control_comp_stmt_anchors_or_invalid_stmt(
            case_node,
            keyword_tokens=info.keyword_tokens,
            parens=info.parens,
            parser=info.parser,
            open_anchor=info.open_anchor,
            close_anchor=info.close_anchor,
            missing_parens_is_error=info.report_missing_parens,
        )
        clear_case_comp_case(case)
        case_nodes.append(case_node)

    match_stmt = ast.Match(
        subject=subject,
        cases=case_nodes,
        **kwargs,
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        match_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            match_stmt,
            ast.Return(
                value=ast.Constant(value=None, **get_pos_attributes(subject)),
                **get_pos_attributes(subject),
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_comp(
    test: ast.expr,
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_comp"
    while_stmt = ast.While(
        test=test,
        body=[
            ast.Expr(ast.Yield(body, **get_pos_attributes(body))),
        ],
        orelse=[],
        **kwargs,
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        while_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[while_stmt],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_if_let_comp(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: ast.expr,
    orelse: ast.expr | None,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__if_let_comp"
    if_stmt = make_if_let(
        "let",
        pattern_subjects,
        cond,
        [ast.Return(value=body, **get_pos_attributes(body))],
        [ast.Return(value=orelse, **get_pos_attributes(orelse))] if orelse else [],
        is_let_else=False,
        **kwargs,
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        if_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[if_stmt],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_let_comp(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: ast.expr,
    keyword_tokens: list[TokenInfo | None],
    parens: tuple[TokenInfo | None, TokenInfo | None],
    parser: Parser,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_let_comp"
    while_stmt = make_while_let(
        pattern_subjects,
        cond,
        [ast.Expr(ast.Yield(value=body, **get_pos_attributes(body)))],
        [],
        **kwargs,
    )
    _set_control_comp_stmt_anchors_or_invalid_stmt(
        while_stmt,
        keyword_tokens=keyword_tokens,
        parens=parens,
        parser=parser,
        open_anchor=open_anchor,
        close_anchor=close_anchor,
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[while_stmt],
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_let_comp(
    assignments: list[tuple[ast.expr, ast.expr | None, ast.expr | None]] | None,
    body: ast.expr,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]] | None = None,
    **kwargs: Unpack[PosAttributes],
):
    control_id = "__let_comp"
    stmts: list[ast.stmt]
    if pattern_subjects is not None:
        stmts = [
            make_if_let(
                "let",
                pattern_subjects=pattern_subjects,
                cond=None,
                body=[ast.Return(value=body, **get_pos_attributes(body))],
                orelse=None,
                is_let_else=True,
                **kwargs,
            )
        ]
    else:
        stmts = [
            cast(
                ast.stmt,
                assign_as_declaration(
                    "let",
                    a,
                    bool(assignments),
                    **pos_attribute_to_range(kwargs),
                ),
            )
            for a in assignments or []
        ]
        stmts.append(
            ast.Return(
                value=body,
                **get_pos_attributes(body),
            )
        )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=stmts,
        returns=None,
        type_comment=None,
        type_params=[],
        close_paren_anchor=None,
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


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
    maybe_name: tuple[TokenInfo, bool] | None,
    open_paren: TokenInfo | None,
    args: ast.arguments | None,
    close_paren: TokenInfo | None,
    # Detect mistake colon due to Python's block colon, or TypeScript return type colon.
    invalid_colon: TokenInfo | None,
    returns: ast.expr | None,
    body: list[ast.stmt],
    type_comment: str | None,
    type_params: list[ast.type_param],
    type_param_commas: list[TokenInfo],
    type_params_trailing_comma: TokenInfo | None,
    type_param_brackets: tuple[TokenInfo, TokenInfo] | None,
    *,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    begin_tokens: list[TokenInfo | None] | None = None,
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    errors: list[SyntaxError] = []
    if not maybe_name:
        start_pos, end_pos = _pos_of_anchor(open_anchor)
        error = parser.build_expected_error("function name", start_pos, end_pos)
        errors.append(error)
        name = get_invalid_name()
    else:
        name, is_usable = maybe_name
        if not is_usable:
            error = parser.build_syntax_error(
                f"keyword '{name.string}' cannot be used as function name.",
                name.start,
                name.end,
            )
            errors.append(error)
            name = get_invalid_name()
    if args is None:
        args = make_arguments(None, [], None, [], None, **get_empty_pos_attributes())
    if invalid_colon:
        if returns:
            error = parser.build_syntax_error(
                "':' is not allowed here.",
                invalid_colon.start,
                invalid_colon.end,
            )
        else:
            error = parser.build_syntax_error(
                "':' is not allowed here, use '->' for function return type.",
                invalid_colon.start,
                invalid_colon.end,
            )
        errors.append(error)
    result = maybe_invalid_stmt(
        parser,
        open_paren,
        close_paren,
        node=make_function_def(
            is_async=is_async,
            is_static=is_static,
            name=name,
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            close_paren_anchor=close_paren,
            **kwargs,
        ),
        open_anchor=open_anchor,
        close_anchor=close_anchor,
        begin_tokens=begin_tokens,
    )
    arg_comma_info = get_function_argument_comma_tokens(args)
    _set_define_block_stmt_anchors(
        result,
        begin_tokens=begin_tokens,
        type_param_brackets=type_param_brackets,
        open_paren=open_paren,
        close_paren=close_paren,
        arg_param_commas=arg_comma_info[0] if arg_comma_info else [],
        arg_trailing_comma=arg_comma_info[1] if arg_comma_info else None,
        type_param_commas=type_param_commas,
        type_params_trailing_comma=type_params_trailing_comma,
        body=body,
    )
    if errors:
        add_error_node(result, errors)
    return result


def recover_maybe_invalid_class_def_raw(
    parser: Parser,
    maybe_name: tuple[TokenInfo, bool] | None,
    bases_parens: tuple[TokenInfo, CallArgs, TokenInfo | None] | None,
    body: list[ast.stmt],
    decorator_list: list[ast.expr],
    type_params: list[ast.type_param],
    type_param_commas: list[TokenInfo],
    type_params_trailing_comma: TokenInfo | None,
    type_param_brackets: tuple[TokenInfo, TokenInfo] | None,
    *,
    open_anchor: PosNode | TokenInfo,
    begin_tokens: list[TokenInfo | None] | None = None,
    **kwargs: Unpack[PosAttributes],
) -> ast.ClassDef:
    open_paren, call_args, close_paren = bases_parens or (
        None,
        CallArgs([], [], [], None),
        None,
    )
    bases = call_args.positionals
    keywords = call_args.keywords
    close_anchor = (
        bases[-1]
        if bases
        else (
            type_params[-1]
            if type_params
            else (maybe_name if isinstance(maybe_name, TokenInfo) else open_anchor)
        )
    )
    error: SyntaxError | None = None
    if not maybe_name:
        start_pos, end_pos = _pos_of_anchor(open_anchor)
        error = parser.build_expected_error("class name", start_pos, end_pos)
        name = get_invalid_name()
    else:
        name, is_usable = maybe_name
        if not is_usable:
            error = parser.build_syntax_error(
                f"keyword '{name.string}' cannot be used as class name.",
                name.start,
                name.end,
            )
            name = get_invalid_name()
    class_def = make_class_def(
        name=name,
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
            begin_tokens=begin_tokens,
        )
    _set_define_block_stmt_anchors(
        class_def,
        begin_tokens=begin_tokens,
        type_param_brackets=type_param_brackets,
        open_paren=open_paren,
        close_paren=close_paren,
        arg_param_commas=call_args.commas,
        arg_trailing_comma=call_args.trailing_comma,
        type_param_commas=type_param_commas,
        type_params_trailing_comma=type_params_trailing_comma,
        body=body,
    )
    if error:
        add_error_node(class_def, [error])
    return class_def


def _token_position_default(
    tok: TokenInfo | str, **kwargs: Unpack[PosAttributes]
) -> tuple[tuple[int, int], tuple[int, int]]:
    if isinstance(tok, TokenInfo):
        return (tok.start, tok.end)
    else:
        return unpack_pos_tuple(kwargs)


def let_pattern_check[T: ast.AST](
    parser: Parser,
    decl_type: TokenInfo | str,
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    node: T,
    **kwargs: Unpack[PosAttributes],
) -> T:
    start_pos, end_pos = _token_position_default(decl_type, **kwargs)
    decl_type_str = decl_type.string if isinstance(decl_type, TokenInfo) else decl_type
    if decl_type_str != "let":
        error = parser.build_syntax_error(
            "declaration pattern must be 'let' declaration", start_pos, end_pos
        )
        add_error_node(node, [error])
    if len(pattern_subjects) == 0:
        error = parser.build_syntax_error(
            "declaration pattern must have at least one pattern", start_pos, end_pos
        )
        add_error_node(node, [error])
    return node


def statement_panic_skip(
    parser: Parser,
    skip: list[TokenInfo],
    sync: TokenInfo | str,
    **kwargs: Unpack[PosAttributes],
) -> list[ast.stmt]:
    if isinstance(sync, TokenInfo):
        skip.append(sync)
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    if skip:
        start_loc = skip[0].start
        end_loc = skip[-1].end
    # Record the skipped tokens for error recovery
    error = parser.build_skip_tokens_error(skip, start_loc, end_loc)
    result = ast.Pass(**kwargs)  # Error holder
    add_error_node(result, [error])
    return [result]


def file_trailing_recovery_error(
    parser: Parser,
    success_body: list[ast.stmt],
    skip: list[TokenInfo],
    **kwargs: Unpack[PosAttributes],
) -> ast.Module:
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    if skip:
        start_loc = skip[0].start
        end_loc = skip[-1].end
    # Record the skipped tokens for error recovery
    error = parser.build_skip_tokens_error(skip, start_loc, end_loc)
    error_node = ast.Pass(**kwargs)  # Error holder
    add_error_node(error_node, [error])
    return ast.Module(body=success_body + [error_node], type_ignores=[])


def expression_bracket_recovery(
    parser: Parser,
    open: TokenInfo,
    comp: TokenInfo | None,
    skip: list[TokenInfo],
    close: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.Constant:
    start_loc = _next_col(open.start)
    end_loc = close.end if close else skip[-1].end if skip else _next_col(start_loc)
    if comp:
        skip.insert(0, comp)
    errors: list[SyntaxError] = []
    if skip:
        error = parser.build_skip_tokens_error(skip, start_loc, end_loc)
        errors.append(error)
        start_loc = _next_col(skip[-1].start)
        end_loc = _next_col(skip[-1].end)
    if not close:
        error = parser.build_expected_error(
            f"closing bracket for '{open.string}'", start_loc, end_loc
        )
        errors.append(error)
    resul = ast.Constant(value=Ellipsis, **kwargs)
    if errors:
        add_error_node(resul, errors)
    return resul


def attribute_access_recovery(
    parser: Parser,
    value: ast.expr,
    access_dot: TokenInfo,
    ctx: ast.expr_context,
    **kwargs: Unpack[PosAttributes],
):
    assert access_dot.string in (".", "?.")
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    error = parser.build_expected_error(
        "attribute name after '.'",
        start_loc,
        (end_loc[0], end_loc[1] + len(access_dot.string)),
    )
    debug_verbose_print(
        lambda: (
            f"Recovering from invalid attribute access: {ast.dump(value)}{access_dot.string} access_dot.string == '.' is {access_dot.string == '.'}"
        )
    )
    if access_dot.string == ".":
        result = copy.deepcopy(value)
        result = ast.Attribute(
            value=value,
            attr="_typh_invalid_attribute",
            ctx=ast.Load(),
            **kwargs,
        )
        add_error_node(result, [error])
        set_completion_trigger_anchor_token(result, access_dot)
        return result
    # "?."
    adjusted_pos = kwargs
    if adjusted_pos["end_col_offset"] is not None:
        adjusted_pos["end_col_offset"] += 2
    access = ast.Attribute(
        value=value,
        attr="_typh_invalid_attribute",
        ctx=ast.Load(),
        **kwargs,
    )
    result = ast.IfExp(
        test=ast.Compare(
            left=value,
            ops=[ast.IsNot()],
            comparators=[ast.Constant(value=None, **adjusted_pos)],
            **get_empty_pos_attributes(),
        ),
        body=access,
        orelse=ast.Constant(value=None, **adjusted_pos),
        **get_empty_pos_attributes(),
    )
    debug_verbose_print(
        lambda: (
            f"Adding error to optional attribute access:\n  value={ast.dump(value)}@{get_pos_attributes(value)},\n  access={ast.dump(access)}@{get_pos_attributes(access)},\n  result={ast.dump(result)}@{get_pos_attributes(result)}"
        )
    )
    set_completion_trigger_anchor_token(access, access_dot)
    add_error_node(result, [error])
    return result


def subscr_recovery(
    parser: Parser,
    value: ast.expr,
    open_bracket: TokenInfo,
    close_bracket: TokenInfo | None,
    ctx: ast.expr_context,
    **kwargs: Unpack[PosAttributes],
):
    assert open_bracket.string in ("[", "?[")
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    error = parser.build_expected_error(
        "subscript expression",
        start_loc,
        (end_loc[0], end_loc[1] + len(open_bracket.string)),
    )
    if open_bracket.string == "[":
        result = ast.Subscript(
            value=value,
            # Hack to get string key completion.
            slice=ast.Constant(value="", **get_empty_pos_attributes()),
            ctx=ctx,
            **kwargs,
        )
        debug_verbose_print(
            lambda: (
                f"Adding error to subscript access:\n  value={ast.dump(value)}@{get_pos_attributes(value)},\n  subscript={ast.dump(result)}@{get_pos_attributes(result)}"
            )
        )
        set_completion_trigger_anchor_token(result, open_bracket)
        add_error_node(result, [error])
        return result
    # "?["
    adjusted_pos = kwargs
    if adjusted_pos["end_col_offset"] is not None:
        adjusted_pos["end_col_offset"] += 2
    body = ast.Subscript(
        value=value,
        # Hack to get string key completion.
        slice=ast.Constant(value="", **get_empty_pos_attributes()),
        ctx=ctx,
        **kwargs,
    )
    result = ast.IfExp(
        test=ast.Compare(
            left=value,
            ops=[ast.IsNot()],
            comparators=[ast.Constant(value=None, **adjusted_pos)],
            **get_empty_pos_attributes(),
        ),
        body=body,
        orelse=ast.Constant(value=None, **adjusted_pos),
        **get_empty_pos_attributes(),
    )
    debug_verbose_print(
        lambda: (
            f"Adding error to optional subscript access:\n  value={ast.dump(value)}@{get_pos_attributes(value)},\n  subscript={ast.dump(body)}@{get_pos_attributes(body)},\n  result={ast.dump(result)}@{get_pos_attributes(result)}"
        )
    )
    set_completion_trigger_anchor_token(body, open_bracket)
    add_error_node(result, [error])
    return result


def maybe_invalid_import_dot_names(
    parser: Parser,
    left_names: ImportDotNames | None,
    name: TokenInfo | None,
    dot: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> ImportDotNames:
    if name:
        if left_names:
            return ImportDotNames(
                names=left_names.names + [name],
                dots=left_names.dots + [dot],
                name_missing_dot_errors=left_names.name_missing_dot_errors,
            )
        else:
            return ImportDotNames(names=[name], dots=[dot], name_missing_dot_errors=[])
    # Missing name error.
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    error = parser.build_expected_error(
        "name after '.'",
        start_loc,
        _next_col(end_loc),
    )
    debug_verbose_print(
        lambda: (
            f"Import name missing after dot: start_loc={start_loc}, end_loc={end_loc}, error={error}"
        )
    )
    return ImportDotNames(
        names=left_names.names if left_names else [],
        dots=left_names.dots if left_names else [],
        name_missing_dot_errors=(
            left_names.name_missing_dot_errors if left_names else []
        )
        + [error],
    )


class _ErrorGather(TyphonASTRawVisitor):
    errors: list[SyntaxError]

    def __init__(self):
        self.errors = []
        super().__init__()

    def visit(self, node: ast.AST):
        if errors := get_error_node(node):
            self.errors.extend(errors)
        self.generic_visit(node)


def gather_errors(node: ast.AST):
    gather = _ErrorGather()
    gather.visit(node)
    parse_errors = sorted(gather.errors, key=lambda e: (e.lineno, e.offset))
    set_syntax_error(node, parse_errors)
