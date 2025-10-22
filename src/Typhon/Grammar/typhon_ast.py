# Ast Extensions for Typhon

import ast
from typing import Union, Unpack, TypedDict, Tuple, cast
from copy import copy
from ..Driver.debugging import debug_print


class PosAttributes(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


class PostAttributesNoneless(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int


def pos_attribute_noneless(pos: PosAttributes) -> PostAttributesNoneless:
    if getattr(pos, "end_lineno", None) is None:
        pos["end_lineno"] = pos["lineno"]
    if getattr(pos, "end_col_offset", None) is None:
        pos["end_col_offset"] = pos["col_offset"]
    return cast(PostAttributesNoneless, pos)


type PosNode = (
    ast.stmt
    | ast.expr
    | ast.alias
    | ast.arg
    | ast.type_param
    | ast.excepthandler
    | ast.pattern
    | ast.keyword
)


def get_pos_attributes(node: PosNode) -> PosAttributes:
    return PosAttributes(
        lineno=node.lineno,
        col_offset=node.col_offset,
        end_lineno=getattr(node, "end_lineno", None),
        end_col_offset=getattr(node, "end_col_offset", None),
    )


def get_empty_pos_attributes() -> PosAttributes:
    return PosAttributes(
        lineno=0,
        col_offset=0,
        end_lineno=0,
        end_col_offset=0,
    )


# Normal assignments, let assignments for variable declarations,
# and constant assignments for constant definitions.
# They all are Assign/AnnAssign in Python, we distinguish them by
# additional attribute which the user can only access by API here.


# Note that inheriting from ast.Assign or ast.AnnAssign is not recommended
# because that breaks AST visitor (e.g.unparse method) that use type name
# directly to distinguish nodes.


def is_decl_stmt(node: ast.AST) -> bool:
    return isinstance(node, (ast.Assign, ast.AnnAssign))


type DeclarableStmt = Union[
    ast.Assign, ast.AnnAssign, ast.withitem, ast.For, ast.AsyncFor, ast.comprehension
]

_IS_VAR = "_typh_is_var"
_IS_LET = "_typh_is_let"
_TYPE_ANNOTATION = "_typh_annotation"
_IS_MULTI_DECL = "_typh_is_multi_decl"
_IS_TYPING_EXPRESSION = "_typh_is_typing_expression"


def is_var(node: DeclarableStmt) -> bool:
    return getattr(node, _IS_VAR, False)


def is_var_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, _IS_VAR, False)


def is_let(node: DeclarableStmt) -> bool:
    return getattr(node, _IS_LET, False)


def is_let_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, _IS_LET, False)


def is_decl_assign(node: ast.AST) -> bool:
    """Check if the node is a declaration assignment (let or var)."""
    return is_var_assign(node) or is_let_assign(node)


def set_is_var(node: DeclarableStmt):
    setattr(node, _IS_VAR, True)


def _set_is_let(node: DeclarableStmt):
    setattr(node, _IS_LET, True)


def _set_is_let_var(node: DeclarableStmt, decl_type: str):
    if decl_type == "var":
        set_is_var(node)
    elif decl_type == "let":
        _set_is_let(node)
    else:
        raise ValueError(f"Unknown declaration type: {decl_type}")


def copy_is_let_var(src: DeclarableStmt, dest: DeclarableStmt) -> None:
    if is_var_assign(src):
        set_is_var(dest)
    if is_let_assign(src):
        _set_is_let(dest)


type PossibleAnnotatedNode = (
    ast.Name
    | ast.withitem
    | ast.For
    | ast.AsyncFor
    | ast.comprehension
    | ast.Starred
    | ast.pattern
)


def set_type_annotation(
    node: PossibleAnnotatedNode, type_node: ast.expr | None
) -> ast.AST:
    debug_print(
        f"set_type_annotation: {ast.dump(node)} to {ast.dump(type_node) if type_node else 'None'}"
    )  # [HN] For debug.
    setattr(node, _TYPE_ANNOTATION, type_node)
    return node


def get_type_annotation(node: PossibleAnnotatedNode) -> ast.expr | None:
    return getattr(node, _TYPE_ANNOTATION, None)


def clear_type_annotation(node: ast.AST) -> None:
    if hasattr(node, _TYPE_ANNOTATION):
        delattr(node, _TYPE_ANNOTATION)


def set_is_multi_decl(node: ast.AST, is_multi: bool = True) -> ast.AST:
    setattr(node, _IS_MULTI_DECL, is_multi)
    return node


def is_multi_decl(node: ast.AST) -> bool:
    return getattr(node, _IS_MULTI_DECL, False)


def clear_is_multi_decl(node: ast.AST) -> None:
    if hasattr(node, _IS_MULTI_DECL):
        delattr(node, _IS_MULTI_DECL)


def set_is_typing_expression(node: ast.expr, is_typing: bool = True) -> ast.expr:
    result = copy(node)  # To avoid chached node is contaminated.
    setattr(result, _IS_TYPING_EXPRESSION, is_typing)
    debug_print(f"set_is_typing_expression: {ast.dump(result)}")  # [HN] For debug.
    return result


def is_typing_expression(node: ast.expr) -> bool:
    return getattr(node, _IS_TYPING_EXPRESSION, False)


def clear_is_typing_expression(node: ast.expr) -> None:
    if hasattr(node, _IS_TYPING_EXPRESSION):
        delattr(node, _IS_TYPING_EXPRESSION)


def assign_as_declaration(
    decl_type: str,
    assign: tuple[ast.expr, ast.expr | None, ast.expr | None],
    is_multi_target: bool,
    lineno: int,
    col_offset: int,
    end_lineno: int,
    end_col_offset: int,
) -> Union[ast.Assign, ast.AnnAssign]:
    [target, annotation, value] = assign

    if annotation is not None:
        result = ast.AnnAssign(
            target=cast(ast.Name, target),
            value=value,
            annotation=annotation,
            simple=1,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    else:
        if value is None:
            # TODO: message
            raise SyntaxError("Declaration must have either annotation or value")
        result = ast.Assign(
            targets=[target],
            value=value,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    _set_is_let_var(result, decl_type)
    if is_multi_target:
        set_is_multi_decl(result, True)
    return result


def get_target_of_declaration(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.expr:
    if isinstance(assign, ast.Assign):
        return assign.targets[0]
    else:
        return assign.target


def _get_tuple_type_elements(type_node: ast.expr) -> list[ast.expr] | None:
    if isinstance(type_node, ast.Tuple):
        return type_node.elts
    elif (
        isinstance(type_node, ast.Subscript)
        and isinstance(type_node.value, ast.Name)
        and type_node.value.id == "tuple"
        and isinstance(type_node.slice, ast.Tuple)
    ):
        return type_node.slice.elts
    return None


def _get_list_type_elements(type_node: ast.expr) -> ast.expr | None:
    if isinstance(type_node, ast.List):
        return type_node.elts[0] if len(type_node.elts) == 1 else None
    elif isinstance(type_node, ast.Subscript):
        debug_print(
            f"_get_list_type_elements: {type_node} value: {type_node.value} id: {type_node.value.id if isinstance(type_node.value, ast.Name) else 'N/A'} slice: {type_node.slice}"
        )  # [HN] For debug.
        if (
            isinstance(type_node.value, ast.Name)
            and type_node.value.id == "list"
            and isinstance(type_node.slice, ast.Name)
        ):
            return type_node.slice
    return None


def _get_list_type(type_node: ast.expr, pos: PosAttributes) -> ast.expr:
    return ast.Subscript(
        value=ast.Name(id="list", **pos),
        slice=type_node,
        ctx=ast.Load(),
        **pos,
    )


def get_annotations_of_declaration_target(
    target: ast.expr,
    type_annotation: ast.expr,
) -> list[tuple[ast.Name, ast.expr | None]]:
    if isinstance(target, ast.Name):
        debug_print(
            f"get_annotations_of_declaration_target ast.Name: {target}, {type_annotation}"
        )  # [HN] For debug.
        return [(target, type_annotation)]
    elif isinstance(target, ast.Tuple):
        debug_print(
            f"get_annotations_of_declaration_target ast.Tuple: {target}, {type_annotation}"
        )  # [HN] For debug.
        type_elts = _get_tuple_type_elements(type_annotation)
        if not type_elts or len(type_elts) != len(target.elts):
            return []
        names = []
        for elt, ty_elt in zip(target.elts, type_elts):
            if isinstance(elt, ast.Name):
                names.append((elt, ty_elt))
            else:
                names.extend(get_annotations_of_declaration_target(elt, ty_elt))
        return names
    elif isinstance(target, ast.List):
        debug_print(
            f"get_annotations_of_declaration_target ast.List: {target}, {type_annotation}"
        )  # [HN] For debug.
        type_elt = _get_list_type_elements(type_annotation)
        if not type_elt:
            return []
        names = []
        for elt in target.elts:
            if isinstance(elt, ast.Name):
                names.append((elt, type_elt))
            else:
                names.extend(get_annotations_of_declaration_target(elt, type_elt))
        return names
    elif isinstance(target, ast.Starred):
        debug_print(
            f"get_annotations_of_declaration_target ast.Starred: {target}, {type_annotation}"
        )  # [HN] For debug.
        return get_annotations_of_declaration_target(
            target.value, _get_list_type(type_annotation, get_pos_attributes(target))
        )
    else:
        # TODO: message
        raise SyntaxError("Invalid target syntax for declaration")


_INLINE_WITH = "_typh_inline_with"


def is_inline_with(node: Union[ast.With, ast.AsyncWith]) -> bool:
    return getattr(node, _INLINE_WITH, False)


def set_inline_with(
    node: Union[ast.With, ast.AsyncWith], is_inline: bool = True
) -> Union[ast.With, ast.AsyncWith]:
    setattr(node, _INLINE_WITH, is_inline)
    return node


def clear_inline_with(node: Union[ast.With, ast.AsyncWith]) -> None:
    if hasattr(node, _INLINE_WITH):
        delattr(node, _INLINE_WITH)


def make_with_stmt(
    is_async: bool,
    items: list[ast.withitem],
    body: list[ast.stmt],
    is_inline: bool,
    **kwargs,
) -> Union[ast.With, ast.AsyncWith]:
    result: Union[ast.With, ast.AsyncWith]
    if is_async:
        result = ast.AsyncWith(items=items, body=body, **kwargs)
    else:
        result = ast.With(items=items, body=body, **kwargs)
    if is_inline:
        set_inline_with(result, True)
    return result


def declaration_as_withitem(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.withitem:
    if isinstance(assign, ast.Assign):
        # TODO when assignment target has several target?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.targets[0])
        copy_is_let_var(assign, item)
        return item
    else:
        if not assign.value:
            raise (SyntaxError)  # TODO: what message?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.target)
        set_type_annotation(item, assign.annotation)
        copy_is_let_var(assign, item)
        return item


# Use Name as a function literal. Replaced to name of FunctionDef.
type FunctionLiteral = ast.Name

_FUNC_DEF = "_typh_func_def"
_IS_FUNCTION_LITERAL = "_typh_is_function_literal"


def get_function_literal_def(name: FunctionLiteral) -> ast.FunctionDef:
    return getattr(name, _FUNC_DEF)


def is_function_literal(name: ast.Name) -> bool:
    return getattr(name, _FUNC_DEF, None) is not None


def set_function_literal_def(
    name: FunctionLiteral, func_def: ast.FunctionDef | ast.AsyncFunctionDef
):
    setattr(name, _FUNC_DEF, func_def)
    setattr(func_def, _IS_FUNCTION_LITERAL, True)


def clear_function_literal_def(name: FunctionLiteral):
    if hasattr(name, _FUNC_DEF):
        delattr(name, _FUNC_DEF)


def is_function_literal_def(func_def: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return getattr(func_def, _IS_FUNCTION_LITERAL, False)


def make_function_literal(
    args: ast.arguments,
    returns: ast.expr,
    body: Union[list[ast.stmt], ast.expr],
    **kwargs: Unpack[PosAttributes],
) -> FunctionLiteral:
    func_id = "__function_literal"  # TODO: Get unique name?
    body_stmts: list[ast.stmt]
    if isinstance(body, list):
        body_stmts = body
    else:
        body_stmts = [
            ast.Return(
                body,
                lineno=body.lineno,
                col_offset=body.col_offset,
                end_lineno=body.end_lineno,
                end_col_offset=body.end_col_offset,
            )
        ]
    func_def = ast.FunctionDef(
        func_id, args, body_stmts, [], returns, type_comment=None, **kwargs
    )
    name = ast.Name(func_id, **kwargs)
    set_function_literal_def(name, func_def)
    return name


# Use Name as a function type. Replaced to name of Protocol.
type FunctionType = ast.Name

_ARG_TYPES = "_typh_arg_types"
_STAR_ARG = "_typh_star_arg"
_STAR_KWDS = "_typh_star_kwds"
_RETURNS = "_typh_returns"


def is_function_type(node: ast.Name) -> bool:
    return getattr(node, _ARG_TYPES, None) is not None


def get_args_of_function_type(node: FunctionType) -> list[ast.arg]:
    return getattr(node, _ARG_TYPES)


def set_args_of_function_type(node: FunctionType, args: list[ast.arg]):
    setattr(node, _ARG_TYPES, args)


def get_star_arg_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _STAR_ARG, None)


def set_star_arg_of_function_type(node: FunctionType, star_arg: ast.arg):
    setattr(node, _STAR_ARG, star_arg)


def get_star_kwds_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _STAR_KWDS, None)


def set_star_kwds_of_function_type(node: FunctionType, star_kwds: ast.arg):
    setattr(node, _STAR_KWDS, star_kwds)


def get_return_of_function_type(node: FunctionType) -> ast.expr | None:
    return getattr(node, _RETURNS, None)


def set_return_of_function_type(node: FunctionType, returns: ast.expr):
    setattr(node, _RETURNS, returns)


fieldsOfFunctionType = [_ARG_TYPES, _STAR_ARG, _STAR_KWDS, _RETURNS]


def clear_function_type(node: FunctionType):
    for field in fieldsOfFunctionType:
        if hasattr(node, field):
            delattr(node, field)


def _check_arrow_type_args(
    args: list[ast.arg],
    star_etc: Tuple[ast.arg, ast.arg] | None,
):
    # TODO* args check (args without name first, with name later, only one star arg, etc)
    kwarg_found = False
    for arg in args:
        if arg.arg.startswith("**"):
            # TODO: Source place
            raise SyntaxError("Only one keyword argument is allowed")
        elif arg.arg.startswith("*"):
            if kwarg_found:
                raise SyntaxError("Keyword argument must be last")
        if len(arg.arg) > 0:
            kwarg_found = True
        else:
            if kwarg_found:
                raise SyntaxError("Non-keyword argument must be first")


def make_arrow_type(
    args: list[ast.arg],
    star_etc: Tuple[ast.arg, ast.arg] | None,
    returns: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> FunctionType:
    # TODO: temporal name
    result = ast.Name("__arrow_type", **kwargs)
    set_args_of_function_type(result, args)
    set_return_of_function_type(result, returns)
    _check_arrow_type_args(args, star_etc)
    if star_etc:
        set_star_arg_of_function_type(result, star_etc[0])
        set_star_kwds_of_function_type(result, star_etc[1])
    return result


def make_arrow_type_single_chain(
    arg: ast.expr,
    star_etc: Tuple[ast.arg, ast.arg] | None,
    returns: list[ast.expr],
    **kwargs: Unpack[PosAttributes],
) -> FunctionType:
    # TODO: temporal name
    result = ast.Name("__arrow_type", **kwargs)
    if len(returns) == 1:
        args = [ast.arg(arg="", annotation=arg, **kwargs)]
        set_args_of_function_type(result, args)
        set_return_of_function_type(result, returns[0])
        _check_arrow_type_args(args, star_etc)
        if star_etc:
            set_star_arg_of_function_type(result, star_etc[0])
            set_star_kwds_of_function_type(result, star_etc[1])
    elif len(returns) == 0:
        raise SyntaxError("Arrow type must have one or more return types")
    else:
        return_type = make_arrow_type_single_chain(
            arg=returns[0],
            star_etc=None,
            returns=returns[1:],
            **kwargs,
        )
        args = [ast.arg(arg="", annotation=arg, **kwargs)]
        set_args_of_function_type(result, args)
        set_return_of_function_type(result, return_type)
        _check_arrow_type_args(args, star_etc)
        if star_etc:
            set_star_arg_of_function_type(result, star_etc[0])
            set_star_kwds_of_function_type(result, star_etc[1])
    return result


def make_for_stmt(
    decl_type: str,
    target: ast.expr,
    type_annotation: ast.expr | None,
    iter: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    type_comment: str | None,
    is_async: bool,
    **kwargs: Unpack[PosAttributes],
) -> Union[ast.For, ast.AsyncFor]:
    if is_async:
        result = ast.AsyncFor(
            target=target,
            iter=iter,
            body=body,
            orelse=orelse or [],
            type_comment=type_comment,
            **kwargs,
        )
        _set_is_let_var(result, decl_type)
        set_type_annotation(result, type_annotation)
        return result
    else:
        result = ast.For(
            target=target,
            iter=iter,
            body=body,
            orelse=orelse or [],
            type_comment=type_comment,
            **kwargs,
        )
        _set_is_let_var(result, decl_type)
        set_type_annotation(result, type_annotation)
        return result


def _make_none_check(name: str, pos: PosAttributes) -> ast.Compare:
    return ast.Compare(
        left=ast.Name(id=name, ctx=ast.Load(), **pos),
        ops=[ast.IsNot()],
        comparators=[ast.Constant(value=None, **pos)],
        **pos,
    )


_LET_PATTERN_BODY = "_typh_multiple_let_pattern_body"
_IS_LET_ELSE = "_typh_is_let_else"


def get_let_pattern_body(node: ast.While | ast.If) -> list[ast.stmt] | None:
    return getattr(node, _LET_PATTERN_BODY, None)


def set_let_pattern_body(
    node: ast.While | ast.If, body: list[ast.stmt]
) -> ast.While | ast.If:
    setattr(node, _LET_PATTERN_BODY, body)
    return node


def clear_let_pattern_body(node: ast.While | ast.If) -> None:
    if hasattr(node, _LET_PATTERN_BODY):
        delattr(node, _LET_PATTERN_BODY)


def is_let_else(node: ast.If | ast.Match) -> bool:
    return getattr(node, _IS_LET_ELSE, False)


def set_is_let_else(node: ast.If | ast.Match, is_let_else: bool) -> ast.stmt:
    setattr(node, _IS_LET_ELSE, is_let_else)
    return node


def clear_is_let_else(node: ast.If | ast.Match) -> None:
    if hasattr(node, _IS_LET_ELSE):
        delattr(node, _IS_LET_ELSE)


def make_if_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    is_let_else: bool,
    **kwargs: Unpack[PosAttributes],
) -> ast.stmt:
    if len(pattern_subjects) == 0:
        raise SyntaxError("if let must have at least one pattern")
    # elif len(pattern_subjects) == 1:
    #     (pattern, subject) = pattern_subjects[0]
    #     return set_is_let_else(
    #         _make_if_let_single(subject, pattern, cond, body, orelse, **kwargs),
    #         is_let_else,
    #     )
    else:
        return set_is_let_else(
            _make_if_let_multiple(pattern_subjects, cond, body, orelse, **kwargs),
            is_let_else,
        )


def _make_if_let_single_case(
    pattern: ast.pattern,
    cond: ast.expr | None,
    body: list[ast.stmt],
    make_none_check: bool,
) -> ast.match_case:
    if (
        isinstance(pattern, ast.MatchAs)
        and pattern.pattern is None
        and pattern.name is not None
        and cond is None
        and make_none_check
    ):
        # Variable capture pattern, e.g. `let x = ...` without condition.
        # In this case, the condition is None check.
        return ast.match_case(
            pattern=pattern,
            guard=_make_none_check(pattern.name, get_pos_attributes(pattern)),
            body=body,
        )
    else:
        return ast.match_case(
            pattern=pattern,
            guard=cond,
            body=body,
        )


def _make_if_let_single(
    subject: ast.expr,
    pattern: ast.pattern,
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.Match:
    cases: list[ast.match_case] = []
    cases.append(_make_if_let_single_case(pattern, cond, body, make_none_check=True))
    # Default wildcard _ case represents orelse clause.
    if orelse:
        cases.append(
            # wildcard _ case.
            ast.match_case(
                pattern=ast.MatchAs(
                    pattern=None, name=None, **pos_attribute_noneless(kwargs)
                ),
                body=orelse or [],
            )
        )
    return ast.Match(subject=subject, cases=cases, **kwargs)


def _make_nested_match_for_multiple_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    **kwargs: Unpack[PosAttributes],
) -> list[ast.stmt]:
    # Build nested match statements from inside out.
    for pattern, subject in reversed(pattern_subjects):
        nested_match: ast.stmt = ast.Match(
            subject=subject,
            cases=[
                _make_if_let_single_case(
                    pattern, cond, body, make_none_check=cond is None
                )
            ],
            **kwargs,
        )
        body = [nested_match]
        cond = None  # Only the innermost match has the condition.
    return body


# Multiple patterns are combined into nested match statements.
def _make_if_let_multiple(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.If:
    """
        if (let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                <patternN> = <subjectN>[;<cond>]) {
            <body>
        } else {
            <orelse>
        }
    --> (temporary represented now)

        if True: # multiple_let_pattern_body set
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
        else:
            <orelse>
    """
    # Build nested match statements from inside out.
    result = ast.If(
        test=ast.Constant(value=True, **kwargs),
        body=_make_nested_match_for_multiple_let(
            pattern_subjects, cond, body, **kwargs
        ),
        orelse=orelse or [],
        **kwargs,
    )
    set_let_pattern_body(result, body)
    return result


def make_while_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.While:
    if len(pattern_subjects) == 0:
        raise SyntaxError("if let must have at least one pattern")
    else:
        return _make_while_let(pattern_subjects, cond, body, orelse, **kwargs)


def _make_while_let(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.While:
    """
        while (let <pattern1> = <subject1>,
                   <pattern2> = <subject2>,
                   ...,
                   <patternN> = <subjectN>
                   [;<cond>]) {
            <body>
        } else {
            <orelse>
        }

    --> (temporary represented now)

        while True: # multiple_let_pattern_body set to <body>
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
        else:
            <orelse>
    """

    result = ast.While(
        test=ast.Constant(value=True, **kwargs),
        body=_make_nested_match_for_multiple_let(
            pattern_subjects, cond, body, **kwargs
        ),
        orelse=orelse or [],
        **kwargs,
    )
    set_let_pattern_body(result, body)
    return result


IS_STATIC = "_typh_is_static"


def set_is_static(node: ast.FunctionDef | ast.AsyncFunctionDef, is_static: bool = True):
    setattr(node, IS_STATIC, is_static)


def is_static(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return getattr(node, IS_STATIC, False)


def make_function_def(
    is_async: bool,
    is_static: bool,
    name: str,
    args: ast.arguments,
    returns: ast.expr | None,
    body: list[ast.stmt],
    type_comment: str | None,
    type_params: list[ast.type_param],
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if is_async:
        result = ast.AsyncFunctionDef(
            name=name,
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            **kwargs,
        )
    else:
        result = ast.FunctionDef(
            name=name,
            args=args,
            returns=returns,
            body=body,
            type_comment=type_comment,
            type_params=type_params,
            **kwargs,
        )
    set_is_static(result, is_static)
    return result


_CONTROL_COMPREHENSION = "_typh_is_control_comprehension"
type ControlComprehension = ast.Name


def get_control_comprehension_def(
    node: ControlComprehension,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return getattr(node, _CONTROL_COMPREHENSION)


def is_control_comprehension(node: ControlComprehension) -> bool:
    return getattr(node, _CONTROL_COMPREHENSION, None) is not None


def set_control_comprehension_def(
    node: ControlComprehension, func_def: ast.FunctionDef | ast.AsyncFunctionDef
):
    setattr(node, _CONTROL_COMPREHENSION, func_def)


def clear_is_control_comprehension(node: ControlComprehension) -> None:
    if hasattr(node, _CONTROL_COMPREHENSION):
        delattr(node, _CONTROL_COMPREHENSION)


# When for-if comprehensions has function literal or other control comprehension,
# it cannot be inline.
class ComprehensionInlineCheckVisitor(ast.NodeVisitor):
    is_inline: bool

    def __init__(self):
        self.is_inline = True

    def visit(self, node: ast.AST):
        if isinstance(node, ast.Name):
            if is_function_literal(node) or is_control_comprehension(node):
                self.is_inline = False
                return  # Stop visiting further.
        super().visit(node)


def _check_comprehension_inline(node: ast.expr) -> bool:
    visitor = ComprehensionInlineCheckVisitor()
    visitor.visit(node)
    return visitor.is_inline


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


def make_comprehension(
    decl_type: str,
    target: ast.expr,
    type_annotation: ast.expr | None,
    iter: ast.expr,
    ifs: list[ast.expr],
    is_async: int,
) -> ast.comprehension:
    clause = ast.comprehension(
        target=target,
        iter=iter,
        ifs=ifs,
        is_async=is_async,
    )
    _set_is_let_var(clause, decl_type)
    set_type_annotation(clause, type_annotation)
    return clause


def _comprehension_function(
    id: str,
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.FunctionDef:
    args = _empty_args()
    body_stmts: list[ast.stmt] = [
        ast.Expr(ast.Yield(value=elt, **get_pos_attributes(elt)))
    ]
    # Build nested for and if statements from inside out.
    for gen in reversed(generators):
        for if_clause in reversed(gen.ifs):
            body_stmts = [
                ast.If(
                    test=if_clause,
                    body=body_stmts,
                    orelse=[],
                    **get_pos_attributes(if_clause),
                )
            ]
        if gen.is_async:
            body_stmts = [
                ast.AsyncFor(
                    target=gen.target,
                    iter=gen.iter,
                    body=body_stmts,
                    orelse=[],
                    **kwargs,
                )
            ]
        else:
            body_stmts = [
                ast.For(
                    target=gen.target,
                    iter=gen.iter,
                    body=body_stmts,
                    orelse=[],
                    **kwargs,
                )
            ]
    func_def = ast.FunctionDef(
        name=id,
        args=args,
        body=body_stmts,
        decorator_list=[],
        returns=None,
        type_comment=None,
        **kwargs,
    )
    return func_def


def make_genexp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if _check_comprehension_inline(elt):
        return ast.GeneratorExp(elt=elt, generators=generators, **kwargs)
    control_id = "__genexp_control"
    # Make a control comprehension to hold the generators.
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    func_def = _comprehension_function(control_id, elt, generators, **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def _ref_genexp(genexp: ast.expr, temp_name: str, is_async: int) -> ast.comprehension:
    return ast.comprehension(
        target=ast.Name(id=temp_name, ctx=ast.Store(), **get_pos_attributes(genexp)),
        iter=genexp,
        ifs=[],
        is_async=is_async,
    )


def make_listcomp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if _check_comprehension_inline(elt):
        return ast.ListComp(elt=elt, generators=generators, **kwargs)
    comp_temp_name = "__listcomp_temp"
    return ast.ListComp(
        elt=ast.Name(id=comp_temp_name, ctx=ast.Load(), **kwargs),
        generators=[
            _ref_genexp(
                make_genexp(elt, generators, **kwargs),
                comp_temp_name,
                generators[0].is_async,
            )
        ],
        **kwargs,
    )


def make_setcomp(
    elt: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if _check_comprehension_inline(elt):
        return ast.SetComp(elt=elt, generators=generators, **kwargs)
    comp_temp_name = "__setcomp_temp"
    return ast.SetComp(
        elt=ast.Name(id=comp_temp_name, ctx=ast.Load(), **kwargs),
        generators=[
            _ref_genexp(
                make_genexp(elt, generators, **kwargs),
                comp_temp_name,
                generators[0].is_async,
            )
        ],
        **kwargs,
    )


def make_dictcomp(
    key: ast.expr,
    value: ast.expr,
    generators: list[ast.comprehension],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    if _check_comprehension_inline(key) and _check_comprehension_inline(value):
        return ast.DictComp(key=key, value=value, generators=generators, **kwargs)
    comp_temp_name_key = "__dictcomp_temp_key"
    comp_temp_name_val = "__dictcomp_temp_val"
    return ast.DictComp(
        key=ast.Name(id=comp_temp_name_key, ctx=ast.Load(), **kwargs),
        value=ast.Name(id=comp_temp_name_val, ctx=ast.Load(), **kwargs),
        generators=[
            ast.comprehension(
                target=ast.Tuple(
                    elts=[
                        ast.Name(id=comp_temp_name_key, ctx=ast.Store(), **kwargs),
                        ast.Name(id=comp_temp_name_val, ctx=ast.Store(), **kwargs),
                    ],
                    ctx=ast.Store(),
                    **get_pos_attributes(key),
                ),
                iter=make_genexp(
                    ast.Tuple(elts=[key, value], ctx=ast.Load(), **kwargs),
                    generators,
                    **kwargs,
                ),
                ifs=[],
                is_async=generators[0].is_async,
            )
        ],
        **kwargs,
    )


def make_with_comp(
    is_async: bool,
    items: list[ast.withitem],
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__with_control"
    func_def = make_function_def(
        is_async=is_async,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.With(
                items=items,
                body=[ast.Return(value=body, **get_pos_attributes(body))],
                **kwargs,
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_try_comp(
    body: ast.expr,
    handlers: list[ast.Name],
    **kwargs: Unpack[PosAttributes],
):
    control_id = "__try_comp"
    handler_blocks = (
        [
            ast.ExceptHandler(
                type=get_try_comp_except(handler)[0],
                name=handler.id if handler.id else None,
                body=[
                    ast.Return(
                        value=get_try_comp_except(handler)[1],
                        **get_pos_attributes(handler),
                    )
                ],
                **get_pos_attributes(handler),
            )
            for handler in handlers
        ]
        if handlers
        else [
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
    )
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.Try(
                body=[ast.Return(value=body, **get_pos_attributes(body))],
                handlers=handler_blocks,
                orelse=[],
                finalbody=[],
                **get_pos_attributes(body),
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        **get_pos_attributes(body),
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


_EXCEPT_COMP = "_typh_is_try_comp_except"


def set_try_comp_except(node: ast.Name, type_body: tuple[ast.expr | None, ast.expr]):
    setattr(node, _EXCEPT_COMP, type_body)


def get_try_comp_except(node: ast.Name) -> tuple[ast.expr | None, ast.expr]:
    return getattr(node, _EXCEPT_COMP)


def make_try_comp_except(
    name: str | None,
    ex_type: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id=name or "", ctx=ast.Load(), **kwargs)
    set_try_comp_except(result, (ex_type, body))
    return result


_CASE_COMP = "_typh_is_case_comp_case"


def set_case_comp_case(
    node: ast.Name, pattern: ast.pattern, guard: ast.expr | None, body: ast.expr
):
    setattr(node, _CASE_COMP, (pattern, guard, body))


def get_case_comp_case(
    node: ast.Name,
) -> tuple[ast.pattern, ast.expr | None, ast.expr]:
    return getattr(node, _CASE_COMP)


def make_match_comp_case(
    pattern: ast.pattern,
    guard: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    result = ast.Name(id="", ctx=ast.Load(), **kwargs)
    set_case_comp_case(result, pattern, guard, body)
    return result


def make_match_comp(
    subject: ast.expr,
    cases: list[ast.Name],
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__match_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.Match(
                subject=subject,
                cases=[
                    ast.match_case(
                        pattern=get_case_comp_case(case)[0],
                        guard=get_case_comp_case(case)[1],
                        body=[
                            ast.Return(
                                value=get_case_comp_case(case)[2],
                                **get_pos_attributes(case),
                            )
                        ],
                    )
                    for case in cases
                ],
                **kwargs,
            ),
            ast.Return(
                value=ast.Constant(value=None, **get_pos_attributes(subject)),
                **get_pos_attributes(subject),
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_comp(
    test: ast.expr,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            ast.While(
                test=test,
                body=[
                    ast.Expr(ast.Yield(body, **get_pos_attributes(body))),
                ],
                orelse=[],
                **kwargs,
            ),
        ],
        returns=None,
        type_comment=None,
        type_params=[],
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
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__if_let_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            make_if_let(
                pattern_subjects,
                cond,
                [ast.Return(value=body, **get_pos_attributes(body))],
                [ast.Return(value=orelse, **get_pos_attributes(orelse))]
                if orelse
                else [],
                is_let_else=False,
                **kwargs,
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_while_let_comp(
    pattern_subjects: list[tuple[ast.pattern, ast.expr]],
    cond: ast.expr | None,
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> ast.expr:
    control_id = "__while_let_comp"
    func_def = make_function_def(
        is_async=False,
        is_static=False,
        name=control_id,
        args=_empty_args(),
        body=[
            make_while_let(
                pattern_subjects,
                cond,
                [ast.Expr(ast.Yield(value=body, **get_pos_attributes(body)))],
                [],
                **kwargs,
            )
        ],
        returns=None,
        type_comment=None,
        type_params=[],
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


def make_let_comp(
    assignments: list[tuple[ast.expr, ast.expr | None, ast.expr | None]],
    body: ast.expr,
    **kwargs: Unpack[PosAttributes],
):
    control_id = "__let_comp"
    stmts: list[ast.stmt] = [
        cast(
            ast.stmt,
            assign_as_declaration(
                "let", a, len(assignments) > 0, **pos_attribute_noneless(kwargs)
            ),
        )
        for a in assignments
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
        **kwargs,
    )
    result = ast.Name(id=control_id, ctx=ast.Load(), **kwargs)
    set_control_comprehension_def(result, func_def)
    return result


IS_OPTIONAL = "_typh_is_optional"
IS_OPTIONAL_PIPE = "_typh_is_optional_pipe"


def maybe_optional(node: ast.expr, operator_string: str) -> ast.expr:
    if operator_string.startswith("?"):
        setattr(node, IS_OPTIONAL, True)
    return node


def set_is_optional(node: ast.expr, is_optional: bool = True) -> ast.expr:
    setattr(node, IS_OPTIONAL, is_optional)
    return node


def is_optional(node: ast.expr) -> bool:
    return getattr(node, IS_OPTIONAL, False)


def clear_is_optional(node: ast.expr) -> None:
    if hasattr(node, IS_OPTIONAL):
        delattr(node, IS_OPTIONAL)


def set_is_optional_pipe(node: ast.expr, is_optional: bool = True) -> ast.expr:
    setattr(node, IS_OPTIONAL_PIPE, is_optional)
    return node


def is_optional_pipe(node: ast.expr) -> bool:
    return getattr(node, IS_OPTIONAL_PIPE, False)


def clear_is_optional_pipe(node: ast.expr) -> None:
    if hasattr(node, IS_OPTIONAL_PIPE):
        delattr(node, IS_OPTIONAL_PIPE)


IS_COALESCING = "_typh_is_coalescing"


def set_is_coalescing(node: ast.Tuple, is_coalescing: bool = True) -> ast.expr:
    ast.Tuple()
    setattr(node, IS_COALESCING, is_coalescing)
    return node


def is_coalescing(node: ast.Tuple) -> bool:
    return getattr(node, IS_COALESCING, False)


UnaryPostfix = ast.Tuple  # Using Tuple node for postfix operators.
OPTIONAL_QUESTION = "_typh_op_optional_question"
FORCE_UNWRAP = "_typh_op_force_unwrap"


def get_optional_question_node(
    node: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> UnaryPostfix:
    result = ast.Tuple(elts=[node], ctx=ast.Load(), **kwargs)
    setattr(result, OPTIONAL_QUESTION, True)
    return result


def is_optional_question(node: ast.expr) -> bool:
    return getattr(node, OPTIONAL_QUESTION, False)


def get_force_unwrap_node(
    node: ast.expr,
    **kwargs: Unpack[PosAttributes],
) -> UnaryPostfix:
    result = ast.Tuple(elts=[node], ctx=ast.Load(), **kwargs)
    setattr(result, FORCE_UNWRAP, True)
    return result


def is_force_unwrap(node: ast.expr) -> bool:
    return getattr(node, FORCE_UNWRAP, False)


def make_pipe_call(
    left: ast.expr, rights: list[tuple[bool, ast.expr]], **kwargs: Unpack[PosAttributes]
) -> ast.expr:
    result: ast.expr = left
    for is_optional, right in rights:
        result = ast.Call(
            func=right,
            args=[result],
            keywords=[],
            **kwargs,
        )
        if is_optional:
            set_is_optional_pipe(result, True)
    return result


_IS_PLACEHOLDER = "_typh_is_placeholder"


def set_is_placeholder(node: ast.Name, is_placeholder: bool = True) -> ast.expr:
    setattr(node, _IS_PLACEHOLDER, is_placeholder)
    return node


def is_placeholder(node: ast.Name) -> bool:
    return getattr(node, _IS_PLACEHOLDER, False)


def clear_is_placeholder(node: ast.Name) -> None:
    if hasattr(node, _IS_PLACEHOLDER):
        delattr(node, _IS_PLACEHOLDER)


_RECORD_LITERAL_FIELDS = "_typh_is_record_literal_fields"
_RECORD_TYPE = "_typh_is_record_literal_type"
_RECORD_PATTERN = "_typh_is_record_pattern"
type RecordLiteral = ast.Name
type RecordType = ast.Name
type RecordPatternClass = ast.Name


def set_record_literal_fields(
    node: RecordLiteral, fields: list[tuple[ast.Name, ast.expr | None, ast.expr]]
) -> ast.expr:
    setattr(node, _RECORD_LITERAL_FIELDS, fields)
    return node


def get_record_literal_fields(
    node: RecordLiteral,
) -> list[tuple[ast.Name, ast.expr | None, ast.expr]] | None:
    return getattr(node, _RECORD_LITERAL_FIELDS, None)


def is_record_literal(node: RecordLiteral) -> bool:
    return getattr(node, _RECORD_LITERAL_FIELDS, None) is not None


def clear_record_literal_fields(node: RecordLiteral) -> None:
    if hasattr(node, _RECORD_LITERAL_FIELDS):
        delattr(node, _RECORD_LITERAL_FIELDS)


def make_record_literal(
    fields: list[tuple[ast.Name, ast.expr | None, ast.expr]],
    **kwargs: Unpack[PosAttributes],
) -> RecordLiteral:
    result = ast.Name(
        id="__record_literal",
        **kwargs,
    )
    set_record_literal_fields(result, fields)
    return result


def set_record_type_fields(
    node: RecordType, fields: list[tuple[ast.Name, ast.expr]]
) -> ast.expr:
    setattr(node, _RECORD_TYPE, fields)
    return node


def get_record_type_fields(
    node: RecordType,
) -> list[tuple[ast.Name, ast.expr]] | None:
    return getattr(node, _RECORD_TYPE, None)


def is_record_type(node: RecordType) -> bool:
    return getattr(node, _RECORD_TYPE, None) is not None


def clear_record_type(node: RecordType) -> None:
    if hasattr(node, _RECORD_TYPE):
        delattr(node, _RECORD_TYPE)


def make_record_type(
    fields: list[tuple[ast.Name, ast.expr]],
    **kwargs: Unpack[PosAttributes],
) -> RecordType:
    result = ast.Name(
        id="__record_type",
        **kwargs,
    )
    set_record_type_fields(result, fields)
    return result


def set_is_record_pattern(node: ast.Name, is_record_pattern: bool) -> ast.expr:
    setattr(node, _RECORD_PATTERN, is_record_pattern)
    return node


def is_record_pattern(node: ast.Name) -> bool:
    return getattr(node, _RECORD_PATTERN, None) is not None


def clear_is_record_pattern(node: ast.Name) -> None:
    if hasattr(node, _RECORD_PATTERN):
        delattr(node, _RECORD_PATTERN)


def make_record_pattern(
    keywords: list[tuple[str, ast.pattern]],
    **kwargs: Unpack[PosAttributes],
) -> ast.MatchClass:
    kwd_attrs = [k for k, _ in keywords]
    kwd_patterns = [
        (
            p
            if p is not None
            # Only name is given, capture by member name.
            else ast.MatchAs(pattern=None, name=k, **pos_attribute_noneless(kwargs))
        )
        for k, p in keywords
    ]
    cls_name = ast.Name(
        id="__record_pattern",
        **kwargs,
    )
    set_is_record_pattern(cls_name, True)
    return ast.MatchClass(
        cls=cls_name,
        patterns=[],
        kwd_attrs=kwd_attrs,
        kwd_patterns=kwd_patterns,
        **pos_attribute_noneless(kwargs),
    )


def if_comp_exp(
    test: ast.expr,
    body: ast.expr,
    orelse: ast.expr | None,
    **kwargs: Unpack[PosAttributes],
) -> ast.IfExp:
    if orelse is None:
        orelse = ast.Constant(value=None, **get_pos_attributes(test))
    return ast.IfExp(test=test, body=body, orelse=orelse, **kwargs)


def get_postfix_operator_temp_name(symbol: str) -> str:
    if symbol == "?":
        return OPTIONAL_QUESTION
    elif symbol == "!":
        return FORCE_UNWRAP
    else:
        raise ValueError(f"Unknown postfix operator symbol: {symbol}")


def add_import_alias_top(mod: ast.Module, from_module: str, name: str, as_name: str):
    # Duplicate import is NOT a problem, but better to avoid it for speed.
    for stmt in mod.body:
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module == from_module:
                for alias in stmt.names:
                    if alias.name == name and alias.asname == as_name:
                        return
        else:
            break  # Only check the top sequence of import statements.
    # Add import at the top.
    import_stmt = ast.ImportFrom(
        module=from_module,
        names=[
            ast.alias(
                name=name,
                asname=as_name,
                **get_empty_pos_attributes(),
            )
        ],
        level=0,
        **get_empty_pos_attributes(),
    )
    mod.body.insert(0, import_stmt)


def is_body_jump_away(body: list[ast.stmt]) -> bool:
    if not body:
        return False
    last_stmt = body[-1]
    return isinstance(last_stmt, (ast.Break, ast.Continue, ast.Return, ast.Raise))
