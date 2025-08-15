# Ast Extensions for Typhon

import ast
from typing import Union, Unpack, TypedDict, Tuple

# Use isinstance checks to distinguish the type of assignments
# Normal assignments, let assignments for variable definitions
# and constant assignments for constant definitions.


class LetAssign(ast.Assign):
    """
    Represents a let assignment in Typhon.
    """

    def __repr__(self):
        return f"Let-{super().__repr__()}"


class LetAnnAssign(ast.AnnAssign):
    """
    Represents a let assignment with type annotation in Typhon.
    """

    def __repr__(self):
        return f"Let-{super().__repr__()}"


class ConstAssign(ast.Assign):
    """
    Represents a constant assignment in Typhon.
    """

    def __repr__(self):
        return f"Const-{super().__repr__()}"


class ConstAnnAssign(ast.AnnAssign):
    """
    Represents a constant assignment with type annotation in Typhon.
    """

    def __repr__(self):
        return f"Const-{super().__repr__()}"


class TypeExpr(ast.expr):
    """
    Represents a type in Typhon. Originally type is represented as ast.expr in Python,
    """

    def __repr__(self):
        return f"TypeExpr-{super().__repr__()}"


def set_type_annotation(node: ast.AST, type_node: ast.expr):
    setattr(node, "type_annotation", type_node)


def get_type_annotation(node: ast.AST):
    return getattr(node, "type_annotation")


def withitem_from_assignment(assign: Union[ast.Assign, ast.AnnAssign]) -> ast.withitem:
    if isinstance(assign, ast.Assign):
        # TODO when assignment target has several target?
        return ast.withitem(context_expr=assign.value, optional_vars=assign.targets[0])
    else:
        if not assign.value:
            raise (SyntaxError)  # TODO: what message?
        result = ast.withitem(context_expr=assign.value, optional_vars=assign.target)
        set_type_annotation(result, assign.annotation)
        return result


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
