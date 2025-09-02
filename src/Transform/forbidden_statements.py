import ast
import builtins
from contextlib import contextmanager
from dataclasses import dataclass

from ..Grammar.typhon_ast import (
    get_pos_attributes,
    is_decl_assign,
)
from ..Grammar.syntax_errors import raise_forbidden_statement_error
from .visitor import TyphonASTVisitor


class ForbiddenStatementChecker(TyphonASTVisitor):
    def visit_Delete(self, node: ast.Delete):
        raise_forbidden_statement_error(
            "`del` statement is forbidden", **get_pos_attributes(node)
        )

    def visit_Global(self, node: ast.Global):
        raise_forbidden_statement_error(
            "`global` statement is forbidden", **get_pos_attributes(node)
        )

    def visit_Nonlocal(self, node: ast.Nonlocal):
        raise_forbidden_statement_error(
            "`nonlocal` statement is forbidden", **get_pos_attributes(node)
        )

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                raise_forbidden_statement_error(
                    "Wildcard import is forbidden",
                    **get_pos_attributes(node),
                )
        return self.generic_visit(node)

    # TODO: Check control statements inside class definition.

    def _is_valid_stmt_in_class(self, node: ast.stmt) -> bool:
        if not (
            isinstance(
                node,
                (
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.Import,
                    ast.AnnAssign,
                    ast.Assign,
                ),
            )
        ):
            return False
        if isinstance(node, (ast.AnnAssign, ast.Assign)):
            if not is_decl_assign(node):
                return False
        return True

    def visit(self, node):
        if isinstance(node, ast.stmt) and isinstance(
            self.parent_python_scopes[-1], ast.ClassDef
        ):
            if not self._is_valid_stmt_in_class(node):
                raise_forbidden_statement_error(
                    "Only class/function definitions, variable declarations, imports and docstring are allowed inside class definition",
                    **get_pos_attributes(node),
                )
        super().visit(node)


def check_forbidden_statements(mod: ast.Module):
    ForbiddenStatementChecker().visit(mod)
