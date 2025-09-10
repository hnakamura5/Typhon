import ast
from ..Grammar.typhon_ast import is_inline_with, clear_inline_with
from .visitor import TyphonASTVisitor, flat_append
from contextlib import contextmanager


class _InlineStatementBlockCaptureGather(TyphonASTVisitor):
    parent_block_scopes: list[tuple[ast.AST, list[ast.stmt]]]
    inline_with_and_parent_block: dict[
        ast.With | ast.AsyncWith, tuple[ast.AST, list[ast.stmt]]
    ]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.parent_block_scopes = []
        self.inline_with_and_parent_block = {}

    @contextmanager
    def block_scope(self, node: ast.AST, body: list[ast.stmt]):
        self.parent_block_scopes.append((node, body))
        yield
        self.parent_block_scopes.pop()

    def _visit_list_scoped(self, node: ast.AST, body: list[ast.stmt]):
        with self.block_scope(node, body):
            for node in body:
                self.visit(node)

    def visit_Module(self, node: ast.Module):
        self._visit_list_scoped(node, node.body)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # No need to visit args
        self._visit_list_scoped(node, node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_list_scoped(node, node.body)

    def visit_If(self, node: ast.If):
        # No need to visit test
        self._visit_list_scoped(node, node.body)
        self._visit_list_scoped(node, node.orelse)

    def visit_For(self, node: ast.For):
        # No need to visit target, iter
        self._visit_list_scoped(node, node.body)
        self._visit_list_scoped(node, node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._visit_list_scoped(node, node.body)
        self._visit_list_scoped(node, node.orelse)

    def visit_While(self, node: ast.While):
        self._visit_list_scoped(node, node.body)
        self._visit_list_scoped(node, node.orelse)

    def _visit_With_AsyncWith(self, node: ast.With | ast.AsyncWith):
        if is_inline_with(node):
            self.inline_with_and_parent_block[node] = self.parent_block_scopes[-1]
        else:
            self._visit_list_scoped(node, node.body)

    def visit_With(self, node: ast.With):
        self._visit_With_AsyncWith(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._visit_With_AsyncWith(node)

    def visit_Try(self, node: ast.Try):
        self._visit_list_scoped(node, node.body)
        for handler in node.handlers:
            self._visit_list_scoped(handler, handler.body)
        self._visit_list_scoped(node, node.orelse)
        self._visit_list_scoped(node, node.finalbody)

    def visit_Case(self, node: ast.match_case):
        self._visit_list_scoped(node, node.body)


# This must run after scope_check_rename.
# This introduces new pseudo scopes, that are not in source code.
def inline_statement_block_capture(module: ast.Module):
    visitor = _InlineStatementBlockCaptureGather(module)
    visitor.run()
    for with_node, (parent_block_node, parent_block_body) in reversed(
        visitor.inline_with_and_parent_block.items()
    ):
        while (with_node not in parent_block_body) and len(parent_block_body) > 0:
            last = parent_block_body[-1]
            if not isinstance(last, ast.With | ast.AsyncWith):
                break
            parent_block_body = last.body

        if with_node not in parent_block_body:
            raise RuntimeError("Parent block not found")  # TODO: proper error handling
        index = parent_block_body.index(with_node)
        # Move the remained stmts into with_node's body
        with_node.body = parent_block_body[index + 1 :]
        # Remove the remained stmts from parent block
        del parent_block_body[index + 1 :]
        clear_inline_with(with_node)
