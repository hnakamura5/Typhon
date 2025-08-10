# Ast Extensions for Typhon

import ast
from typing import Union

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
