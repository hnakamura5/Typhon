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


DeclarationType = Union[ast.Assign, ast.AnnAssign, ast.withitem]


def is_let(node: DeclarationType) -> bool:
    return getattr(node, "is_let", False)


def is_let_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_let", False)


def is_const(node: DeclarationType) -> bool:
    return getattr(node, "is_const", False)


def is_const_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_const", False)


def is_decl_assign(node: ast.AST) -> bool:
    """Check if the node is a declaration assignment (let or const)."""
    return is_let_assign(node) or is_const_assign(node)


def _set_is_let(node: DeclarationType):
    setattr(node, "is_let", True)


def _set_is_const(node: DeclarationType):
    setattr(node, "is_const", True)


def copy_is_let_const(src: DeclarationType, dest: DeclarationType) -> None:
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
    if decl_type == "let":
        _set_is_let(result)
    elif decl_type == "const":
        _set_is_const(result)
    else:
        raise ValueError(f"Unknown declaration type: {decl_type}")
    return result


def set_type_annotation(node: ast.AST, type_node: ast.expr):
    setattr(node, "type_annotation", type_node)


def get_type_annotation(node: ast.AST):
    return getattr(node, "type_annotation")


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


def get_function_literal_def(name: ast.Name) -> ast.FunctionDef:
    return getattr(name, "func_def")


def is_function_literal(name: ast.Name) -> bool:
    return getattr(name, "func_def", None) is not None


def set_function_literal_def(name: ast.Name, func_def: ast.FunctionDef):
    setattr(name, "func_def", func_def)


def make_function_literal(
    args: ast.arguments,
    returns: ast.expr,
    body: Union[list[ast.stmt], ast.expr],
    **kwargs: Unpack[PosAttributes],
) -> ast.Name:
    func_id = "temp"  # TODO: Get unique name
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


def is_function_type(node: ast.Name) -> bool:
    return getattr(node, "arg_types", None) is not None


def get_args_of_function_type(node: ast.Name) -> list[ast.arg]:
    return getattr(node, "arg_types")


def set_args_of_function_type(node: ast.Name, args: list[ast.arg]):
    setattr(node, "arg_types", args)


def get_star_arg_of_function_type(node: ast.Name) -> ast.arg | None:
    return getattr(node, "star_arg", None)


def set_star_arg_of_function_type(node: ast.Name, star_arg: ast.arg):
    setattr(node, "star_arg", star_arg)


def get_star_kwds_of_function_type(node: ast.Name) -> ast.arg | None:
    return getattr(node, "star_kwds", None)


def set_star_kwds_of_function_type(node: ast.Name, star_kwds: ast.arg):
    setattr(node, "star_kwds", star_kwds)


def make_arrow_type(
    args: list[ast.arg], star_etc: Tuple[ast.arg, ast.arg] | None, returns: ast.expr
) -> ast.expr:
    # TODO: temporal name
    result = ast.Name("arrow_type")
    set_args_of_function_type(result, args)
    if star_etc:
        set_star_arg_of_function_type(result, star_etc[0])
        set_star_kwds_of_function_type(result, star_etc[1])
    return result
