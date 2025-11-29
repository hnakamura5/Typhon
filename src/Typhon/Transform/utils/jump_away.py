from ...Grammar.typhon_ast import is_case_irrefutable
import ast
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class _Loop:
    node: ast.AST
    is_breaked: bool = False


class _JumpAwayVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.loops: list[_Loop] = []

    @contextmanager
    def loop(self, node: ast.AST):
        self.loops.append(_Loop(node))
        yield
        self.loops.pop()

    def visit_stmt_list(self, stmts: list[ast.stmt]) -> bool:
        for stmt in stmts:
            if self.visit(stmt):
                return True
        return False

    def generic_visit(self, node: ast.AST):
        jump_away = False
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                jump_away |= self.visit_stmt_list(value)
            elif isinstance(value, ast.AST):
                jump_away |= self.visit(value)
        return jump_away

    def visit_Break(self, node: ast.Break):
        if self.loops:
            self.loops[-1].is_breaked = True
            return False
        return True

    def visit_Continue(self, node: ast.Continue):
        if self.loops:
            return False  # This is path to loop header, that pass does not jump away.
        return True

    def visit_Return(self, node: ast.Return):
        return True

    def visit_Raise(self, node: ast.Raise):
        return True

    def visit_If(self, node: ast.If):
        return self.visit_stmt_list(node.body) and self.visit_stmt_list(node.orelse)

    def visit_For(self, node: ast.For):
        with self.loop(node):
            self.visit_stmt_list(node.body)
            if self.loops[-1].is_breaked:
                return False
        return self.visit_stmt_list(node.orelse)

    def visit_While(self, node: ast.While):
        with self.loop(node):
            self.visit_stmt_list(node.body)
            if self.loops[-1].is_breaked:
                return False
        return self.visit_stmt_list(node.orelse)

    def visit_Try(self, node: ast.Try):
        jump_away = self.visit_stmt_list(node.body) or self.visit_stmt_list(node.orelse)
        for handler in node.handlers:
            # TODO: Analyze except types?
            # Currently all handler must jump away to consider try jumps away.
            jump_away &= self.visit_stmt_list(handler.body)
        # Jump away from finally is not allowed.
        return jump_away

    def visit_Match(self, node: ast.Match):
        jump_away = True
        found_irrefutable = False
        for case in node.cases:
            if is_case_irrefutable(case):
                found_irrefutable = True
            jump_away &= self.visit_stmt_list(case.body)
        return jump_away and found_irrefutable


def is_body_jump_away(body: list[ast.stmt]) -> bool:
    visitor = _JumpAwayVisitor()
    return visitor.visit_stmt_list(body)
