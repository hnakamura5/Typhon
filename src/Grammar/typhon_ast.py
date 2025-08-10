# Ast Extensions for Typhon

import ast
from typing import Union

# Normal assignments, let assignments for variable declarations,
# and constant assignments for constant definitions.
# They all are Assign/AnnAssign in Python, we distinguish them by
# additional attribute which the user can only access by API here.


# Note that inheriting from ast.Assign or ast.AnnAssign is not recommended
# because that breaks AST visitor (e.g.unparse method) that use type name
# directly to distinguish nodes.


def is_decl_stmt(node: ast.AST) -> bool:
    return isinstance(node, (ast.Assign, ast.AnnAssign))


def is_let_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_let", False)


def is_const_assign(node: ast.AST) -> bool:
    if not is_decl_stmt(node):
        return False
    return getattr(node, "is_const", False)


def is_decl_assign(node: ast.AST) -> bool:
    """Check if the node is a declaration assignment (let or const)."""
    return is_let_assign(node) or is_const_assign(node)


def _set_is_let(node: Union[ast.Assign, ast.AnnAssign]):
    setattr(node, "is_let", True)


def _set_is_const(node: Union[ast.Assign, ast.AnnAssign]):
    setattr(node, "is_const", True)


def assign_as_declaration(
    decl_type: str,
    assign: Union[ast.Assign, ast.AnnAssign],
    lineno: int,
    col_offset: int,
    end_lineno: int,
    end_col_offset: int,
) -> ast.AST:
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


def withitem_from_assignment(assign: Union[ast.Assign, ast.AnnAssign]):
    if isinstance(assign, ast.Assign):
        # TODO when assignment target has several target?
        return ast.withitem(context_expr=assign.value, optional_vars=assign.targets[0])
    else:
        if not assign.value:
            raise (SyntaxError)  # TODO: what message?
        result = ast.withitem(context_expr=assign.value, optional_vars=assign.target)
        set_type_annotation(result, assign.annotation)
        return result
