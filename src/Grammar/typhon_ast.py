# Ast Extensions for Typhon

import ast
from typing import Union, Unpack, TypedDict, Tuple

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
    ast.Assign, ast.AnnAssign, ast.withitem, ast.For, ast.AsyncFor
]


def is_let(node: DeclarableStmt) -> bool:
    return getattr(node, "is_let", False)


def is_let_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_let", False)


def is_const(node: DeclarableStmt) -> bool:
    return getattr(node, "is_const", False)


def is_const_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_const", False)


def is_decl_assign(node: ast.AST) -> bool:
    """Check if the node is a declaration assignment (let or const)."""
    return is_let_assign(node) or is_const_assign(node)


def _set_is_let(node: DeclarableStmt):
    setattr(node, "is_let", True)


def _set_is_const(node: DeclarableStmt):
    setattr(node, "is_const", True)


def _set_is_let_const(node: DeclarableStmt, decl_type: str):
    if decl_type == "let":
        _set_is_let(node)
    elif decl_type == "const":
        _set_is_const(node)
    else:
        raise ValueError(f"Unknown declaration type: {decl_type}")


def copy_is_let_const(src: DeclarableStmt, dest: DeclarableStmt) -> None:
    if is_let_assign(src):
        _set_is_let(dest)
    if is_const_assign(src):
        _set_is_const(dest)


def assign_as_declaration(
    decl_type: str,
    assign: Union[ast.Assign, ast.AnnAssign],
    lineno: int,
    col_offset: int,
    end_lineno: int,
    end_col_offset: int,
) -> Union[ast.Assign, ast.AnnAssign]:
    if isinstance(assign, ast.AnnAssign):
        result = ast.AnnAssign(
            target=assign.target,
            annotation=assign.annotation,
            value=assign.value,
            simple=assign.simple,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    else:
        result = ast.Assign(
            targets=assign.targets,
            value=assign.value,
            type_comment=assign.type_comment,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
    _set_is_let_const(result, decl_type)
    return result


def set_type_annotation(node: ast.AST, type_node: ast.expr | None) -> None:
    setattr(node, "type_annotation", type_node)


def get_type_annotation(node: ast.AST) -> ast.expr | None:
    return getattr(node, "type_annotation", None)


def declaration_as_withitem(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.withitem:
    if isinstance(assign, ast.Assign):
        # TODO when assignment target has several target?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.targets[0])
        copy_is_let_const(assign, item)
        return item
    else:
        if not assign.value:
            raise (SyntaxError)  # TODO: what message?
        item = ast.withitem(context_expr=assign.value, optional_vars=assign.target)
        set_type_annotation(item, assign.annotation)
        copy_is_let_const(assign, item)
        return item


class PosAttributes(TypedDict):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


type PosNode = ast.stmt | ast.expr | ast.alias | ast.arg | ast.type_param


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


# Use Name as a function literal. Replaced to name of FunctionDef.
type FunctionLiteral = ast.Name


def get_function_literal_def(name: FunctionLiteral) -> ast.FunctionDef:
    return getattr(name, "func_def")


def is_function_literal(name: ast.Name) -> bool:
    return getattr(name, "func_def", None) is not None


def set_function_literal_def(name: FunctionLiteral, func_def: ast.FunctionDef):
    setattr(name, "func_def", func_def)


def clear_function_literal_def(name: FunctionLiteral):
    if hasattr(name, "func_def"):
        delattr(name, "func_def")


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

_arg_types = "arg_types"
_star_arg = "star_arg"
_star_kwds = "star_kwds"
_returns = "returns"


def is_function_type(node: ast.Name) -> bool:
    return getattr(node, _arg_types, None) is not None


def get_args_of_function_type(node: FunctionType) -> list[ast.arg]:
    return getattr(node, _arg_types)


def set_args_of_function_type(node: FunctionType, args: list[ast.arg]):
    setattr(node, _arg_types, args)


def get_star_arg_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _star_arg, None)


def set_star_arg_of_function_type(node: FunctionType, star_arg: ast.arg):
    setattr(node, _star_arg, star_arg)


def get_star_kwds_of_function_type(node: FunctionType) -> ast.arg | None:
    return getattr(node, _star_kwds, None)


def set_star_kwds_of_function_type(node: FunctionType, star_kwds: ast.arg):
    setattr(node, _star_kwds, star_kwds)


def get_return_of_function_type(node: FunctionType) -> ast.expr | None:
    return getattr(node, _returns, None)


def set_return_of_function_type(node: FunctionType, returns: ast.expr):
    setattr(node, _returns, returns)


fieldsOfFunctionType = [_arg_types, _star_arg, _star_kwds, _returns]


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
        _set_is_let_const(result, decl_type)
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
        _set_is_let_const(result, decl_type)
        set_type_annotation(result, type_annotation)
        return result
