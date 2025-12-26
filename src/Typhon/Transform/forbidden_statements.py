import ast
import builtins
from contextlib import contextmanager
from dataclasses import dataclass

from ..Grammar.typhon_ast import (
    get_pos_attributes,
    is_decl_assign,
    is_multi_decl,
    PosAttributes,
    is_let_else,
    is_inline_with,
)
from ..Grammar.syntax_errors import (
    raise_forbidden_statement_error,
    try_handle_syntax_error_or,
)
from .visitor import TyphonASTVisitor


class ForbiddenStatementChecker(TyphonASTVisitor):
    def _raise_forbidden_statement(self, message: str, pos: PosAttributes):
        try_handle_syntax_error_or(
            None,
            self.module,
            lambda: raise_forbidden_statement_error(message, **pos),
        )

    def visit_Delete(self, node: ast.Delete):
        self._raise_forbidden_statement(
            "`del` statement is forbidden", get_pos_attributes(node)
        )

    def visit_Global(self, node: ast.Global):
        self._raise_forbidden_statement(
            "`global` statement is forbidden", get_pos_attributes(node)
        )

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self._raise_forbidden_statement(
            "`nonlocal` statement is forbidden", get_pos_attributes(node)
        )

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                self._raise_forbidden_statement(
                    "Wildcard import is forbidden",
                    get_pos_attributes(node),
                )
        return self.generic_visit(node)

    def visit_With_AsyncWith(self, node: ast.With | ast.AsyncWith):
        if is_inline_with(node) and self.now_is_top_level():
            self._raise_forbidden_statement(
                "Inline `with` statement in module top level is forbidden",
                get_pos_attributes(node),
            )
        return self.generic_visit(node)

    def visit_With(self, node: ast.With):
        self.visit_With_AsyncWith(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.visit_With_AsyncWith(node)

    def visit_If(self, node: ast.If):
        if is_let_else(node) and self.now_is_top_level() and node.orelse:
            self._raise_forbidden_statement(
                "`let-else` statement in module top level is forbidden",
                get_pos_attributes(node),
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
                    ast.Pass,
                ),
            )
        ):
            return False
        return True

    # Only single variable declaration is allowed inside class definition.
    def is_valid_assignment_in_class(self, node: ast.Assign | ast.AnnAssign) -> bool:
        if not is_decl_assign(node):
            return False
        if is_multi_decl(node):
            return False
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                return False
            if not isinstance(node.targets[0], ast.Name):
                return False
            return True
        if isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name):
                return False
            return True
        return False

    def visit(self, node: ast.AST):
        if isinstance(node, ast.stmt) and isinstance(
            self.parent_python_scopes[-1], ast.ClassDef
        ):
            if not self._is_valid_stmt_in_class(node):
                self._raise_forbidden_statement(
                    "Only class/function definitions, variable declarations, imports and docstring are allowed inside class definition",
                    get_pos_attributes(node),
                )
            if isinstance(node, (ast.AnnAssign, ast.Assign)):
                if not self.is_valid_assignment_in_class(node):
                    self._raise_forbidden_statement(
                        "Only single variable declaration is allowed inside class definition",
                        get_pos_attributes(node),
                    )
        super().visit(node)


def check_forbidden_statements(mod: ast.Module):
    ForbiddenStatementChecker(mod).run()
