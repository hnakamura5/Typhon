# Ast Extensions for Typhon

import ast
from typing import Union, Unpack, TypedDict, Tuple, cast


class PosAttributes(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


type PosNode = (
    ast.stmt
    | ast.expr
    | ast.alias
    | ast.arg
    | ast.type_param
    | ast.excepthandler
    | ast.pattern
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


def _set_is_var(node: DeclarableStmt):
    setattr(node, _IS_VAR, True)


def _set_is_let(node: DeclarableStmt):
    setattr(node, _IS_LET, True)


def _set_is_let_var(node: DeclarableStmt, decl_type: str):
    if decl_type == "var":
        _set_is_var(node)
    elif decl_type == "let":
        _set_is_let(node)
    else:
        raise ValueError(f"Unknown declaration type: {decl_type}")


def copy_is_let_var(src: DeclarableStmt, dest: DeclarableStmt) -> None:
    if is_var_assign(src):
        _set_is_var(dest)
    if is_let_assign(src):
        _set_is_let(dest)


def set_type_annotation(node: ast.AST, type_node: ast.expr | None) -> None:
    setattr(node, _TYPE_ANNOTATION, type_node)


def get_type_annotation(node: ast.AST) -> ast.expr | None:
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
    setattr(node, _IS_TYPING_EXPRESSION, is_typing)
    return node


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
        print(
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
        print(
            f"get_annotations_of_declaration_target ast.Name: {target}, {type_annotation}"
        )  # [HN] For debug.
        return [(target, type_annotation)]
    elif isinstance(target, ast.Tuple):
        print(
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
        print(
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
        print(
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
    if not body:
        body = [ast.Pass(**kwargs)]
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


IS_OPTIONAL = "_typh_is_optional"


def maybe_optional(node: ast.expr, operator_string: str) -> ast.expr:
    ast.IfExp
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


def get_postfix_operator_temp_name(symbol: str) -> str:
    if symbol == "?":
        return OPTIONAL_QUESTION
    elif symbol == "!":
        return FORCE_UNWRAP
    else:
        raise ValueError(f"Unknown postfix operator symbol: {symbol}")
