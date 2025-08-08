# Ast Extensions for Typhon

import ast

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
