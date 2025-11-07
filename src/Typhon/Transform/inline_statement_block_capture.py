import ast
from ..Grammar.typhon_ast import (
    is_inline_with,
    clear_inline_with,
    is_let_else,
    get_let_pattern_body,
)
from .visitor import TyphonASTVisitor, flat_append
from contextlib import contextmanager
from dataclasses import dataclass
from ..Driver.debugging import debug_print, debug_verbose_print
from .utils import is_body_jump_away


@dataclass
class InlineStatement:
    node: ast.With | ast.AsyncWith | ast.If
    parent_block: ast.AST
    parent_block_body: list[ast.stmt]
    body_capture_into: list[ast.stmt]


class _InlineStatementBlockCaptureGather(TyphonASTVisitor):
    parent_block_scopes: list[tuple[ast.AST, list[ast.stmt]]]
    inline_statement_and_parent_block: dict[
        ast.With | ast.AsyncWith | ast.If, InlineStatement
    ]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.parent_block_scopes = []
        self.inline_statement_and_parent_block = {}

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
        """
        # let-else
            let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                <patternN> = <subjectN> else {
                <orelse> # Must jump away.
            }
            <after>

        --> (is represented here in my mind)

            if (let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                    <patternN> = <subjectN>) {
                # empty
            } else {
                <orelse> # Must jump away.
            }
            <after>

        --> (is represented here actually)

            if True: # multiple_let_pattern_body set to empty
                match <subject1>:
                    case <pattern1>:
                        match <subject2>:
                            ...
                                match <subjectN>:
                                    case <patternN>:
                                        # empty
            else:
                <orelse> # Must jump away.
            <after>

        --> (transformation here in my mind)

            if (let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                    <patternN> = <subjectN>) {
                <after>
            } else {
                <orelse> # Must jump away.
            }

        --> (transformation here actually)

            if True: # multiple_let_pattern_body set to empty
                match <subject1>:
                    case <pattern1>:
                        match <subject2>:
                            ...
                                match <subjectN>:
                                    case <patternN>:
                                        <after>
            else:
                <orelse> # Must jump away.
        """
        body = get_let_pattern_body(node)
        if body is None or not is_let_else(node):
            self._visit_list_scoped(node, node.body)
            self._visit_list_scoped(node, node.orelse)
            return
        # let-else
        [parent_block_node, parent_block_body] = self.parent_block_scopes[-1]
        self.inline_statement_and_parent_block[node] = InlineStatement(
            node=node,
            parent_block=parent_block_node,
            parent_block_body=parent_block_body,
            body_capture_into=body,
        )
        debug_print(
            f"Found let else: \n    node:{ast.dump(node)} \n        parent:{ast.dump(parent_block_node)}\n            body:{list(map(ast.dump, body))}"
        )
        if not is_body_jump_away(node.orelse):
            raise RuntimeError(
                "let-else's else body must jump away"
            )  # TODO: Arrow NoReturn function call
        self._visit_list_scoped(node, node.orelse)
        # Hack to make parent of the followings to case's body
        self.parent_block_scopes[-1] = (node, body)

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
        """
        # Inline with
            with let f = open('file.txt')
            <after>

        --> (is represented here)

            with (let f = open('file.txt')) { # is_inline_with
                # empty
            }
            <after>

        --> (transformation here)

            with (let f = open('file.txt')) {
                <after>
            }

        """
        if is_inline_with(node):
            [parent_block_node, parent_block_body] = self.parent_block_scopes[-1]
            self.inline_statement_and_parent_block[node] = InlineStatement(
                node=node,
                parent_block=parent_block_node,
                parent_block_body=parent_block_body,
                body_capture_into=node.body,
            )
            debug_print(
                f"Found inline with: {ast.dump(node)} \n    parent:{ast.dump(parent_block_node)}\n        body:{list(map(ast.dump, node.body))}"
            )
            # Hack to make parent of the followings to with's body
            self.parent_block_scopes[-1] = (node, node.body)
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


# This must run before scope_check_rename.
# This introduces new pseudo scopes, that are not in source code.
# Targets:
# - Inline `with` statement.
# - `let-else` statement.
def inline_statement_block_capture(module: ast.Module):
    visitor = _InlineStatementBlockCaptureGather(module)
    visitor.run()
    for node, inline_node in visitor.inline_statement_and_parent_block.items():
        # parent_block_node = inline_node.parent_block_body
        parent_block_body = inline_node.parent_block_body
        body_capture_into = inline_node.body_capture_into
        debug_print(
            f"Move: node:{ast.dump(node)} \n    inline_node:{ast.dump(inline_node.node)} \n        parent:{list(map(ast.dump, parent_block_body))}\n    body_capture_into:{list(map(ast.dump, body_capture_into))}"
        )
        if node not in parent_block_body:
            raise RuntimeError("Parent block not found")  # TODO: proper error handling
        index = parent_block_body.index(node)
        # Move the remained stmts into with_node's body
        body_capture_into.clear()
        body_capture_into.extend(parent_block_body[index + 1 :])
        # Remove the remained stmts from parent block
        del parent_block_body[index + 1 :]
        debug_verbose_print(
            f"After move: node:{ast.dump(node)}\n    body_capture_into:{list(map(ast.dump, body_capture_into))} \n        parent:{list(map(ast.dump, parent_block_body))}"
        )
