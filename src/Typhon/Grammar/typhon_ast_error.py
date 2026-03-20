import ast
import copy
from dataclasses import dataclass
from typing import Unpack, cast
from tokenize import TokenInfo
from .position import (
    PosAttributes,
    get_empty_pos_attributes,
    unpack_pos_default,
    get_pos_attributes,
    PosNode,
    unpack_pos_tuple,
)
from .typhon_ast import (
    ImportDotNames,
    make_arguments,
    make_for_let_pattern,
    make_function_def,
    make_class_def,
    get_invalid_name,
)
from ..Driver.debugging import debug_print, debug_verbose_print
from .parser_helper import Parser
from .syntax_errors import set_syntax_error, add_error_node, get_error_node
from ..Transform.visitor import TyphonASTRawVisitor


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
            lambda: (
                f"open paren missing: {start_loc} to {end_loc} open anchor: {open_anchor}"
            )
        )
        error = parser.build_expected_error("'('", start_loc, end_loc)
        add_error_node(node, [error])
    if close_paren is None:
        start_loc, end_loc = _pos_of_anchor(close_anchor)
        debug_print(
            lambda: (
                f"close paren missing: {start_loc} to {end_loc} close anchor: {close_anchor}"
            )
        )
        error = parser.build_expected_error("')'", start_loc, end_loc)
        add_error_node(node, [error])
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
    returns: ast.expr | None,
    body: list[ast.stmt],
    type_comment: str | None,
    type_params: list[ast.type_param],
    *,
    open_anchor: PosNode | TokenInfo,
    close_anchor: PosNode | TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    error: SyntaxError | None = None
    if not maybe_name:
        start_pos, end_pos = _pos_of_anchor(open_anchor)
        error = parser.build_expected_error("function name", start_pos, end_pos)
        name = get_invalid_name()
    else:
        name, is_usable = maybe_name
        if not is_usable:
            error = parser.build_syntax_error(
                f"keyword '{name.string}' cannot be used as function name",
                name.start,
                name.end,
            )
            name = get_invalid_name()
    if args is None:
        args = make_arguments(None, [], None, [], None, **get_empty_pos_attributes())
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
    )
    if error:
        add_error_node(result, [error])
    return result


def recover_maybe_invalid_class_def_raw(
    parser: Parser,
    maybe_name: tuple[TokenInfo, bool] | None,
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
    open_paren, (bases, keywords), close_paren = bases_parens or (None, ([], []), None)
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
                f"keyword '{name.string}' cannot be used as class name",
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
    close: TokenInfo,
    **kwargs: Unpack[PosAttributes],
) -> ast.Constant:
    start_loc = open.start
    end_loc = close.end
    if comp:
        skip.insert(0, comp)
    error = parser.build_skip_tokens_error(skip, start_loc, end_loc)
    resul = ast.Constant(value=Ellipsis, **kwargs)
    add_error_node(resul, [error])
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
    debug_verbose_print(
        lambda: (
            f"Recovering from invalid subscript access: {ast.dump(value)}{open_bracket.string}"
        )
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
    add_error_node(result, [error])
    return result


def maybe_invalid_import_dot_names(
    parser: Parser,
    names: ImportDotNames | None,
    name: TokenInfo | None,
    **kwargs: Unpack[PosAttributes],
) -> ImportDotNames:
    if name:
        if names:
            return ImportDotNames(
                names=names.names + [name],
                name_missing_dot_errors=names.name_missing_dot_errors,
            )
        else:
            return ImportDotNames(names=[name], name_missing_dot_errors=[])
    # Missing name error.
    start_loc, end_loc = unpack_pos_tuple(kwargs)
    error = parser.build_expected_error(
        "name after '.'",
        start_loc,
        (end_loc[0], end_loc[1] + 1),
    )
    debug_verbose_print(
        lambda: (
            f"Import name missing after dot: start_loc={start_loc}, end_loc={end_loc}, error={error}"
        )
    )
    return ImportDotNames(
        names=names.names if names else [],
        name_missing_dot_errors=(names.name_missing_dot_errors if names else [])
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
