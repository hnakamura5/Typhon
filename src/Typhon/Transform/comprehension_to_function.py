import ast
from ..Grammar.typhon_ast import (
    clear_is_control_comprehension,
    get_control_comprehension_def,
    get_pos_attributes,
    ControlComprehension,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append
from dataclasses import dataclass
from typing import override
from ..Driver.debugging import debug_print


@dataclass
class Comprehension:
    comprehension: ast.expr


class _Gather(TyphonASTVisitor):
    comprehensions_to_process: list[tuple[ControlComprehension, ast.stmt]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.comprehensions_to_process = []

    def visit_ControlComprehension(self, node: ControlComprehension):
        debug_print(f"comprehension_to_function _Gather visit: {node} {node.__dict__}")
        self.comprehensions_to_process.append((node, self.parent_stmts[-1]))
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    parent_stmt_to_comprehensions: dict[ast.stmt, list[ControlComprehension]]

    def __init__(
        self,
        module: ast.Module,
        parent_stmt_to_comprehensions: dict[ast.stmt, list[ControlComprehension]],
    ):
        super().__init__(module)
        self.parent_stmt_to_comprehensions = parent_stmt_to_comprehensions

    @override
    def visit(self, node: ast.AST):
        if not isinstance(node, ast.stmt):
            return super().visit(node)
        result: list[ast.AST] = []
        if node in self.parent_stmt_to_comprehensions:
            for comp in self.parent_stmt_to_comprehensions[node]:
                func_def = get_control_comprehension_def(comp)
                func_def.name = self.new_control_comprehension_name()
                comp.id = func_def.name
                flat_append(result, self.visit(func_def))
        node_result = super().visit(node)
        flat_append(result, node_result)
        return result

    def visit_ControlComprehension(self, node: ControlComprehension):
        clear_is_control_comprehension(node)
        return ast.Call(
            func=node,
            args=[],
            keywords=[],
            **get_pos_attributes(node),
        )


def comprehension_to_function(module: ast.Module):
    gatherer = _Gather(module)
    gatherer.run()
    parent_stmt_to_comprehensions: dict[ast.stmt, list[ControlComprehension]] = {}
    # parent_stmt_to_comprehensions only with to_be_replaced FROM outer
    for comp, parent_stmt in gatherer.comprehensions_to_process:
        parent_stmt_to_comprehensions.setdefault(parent_stmt, []).append(comp)
    _Transform(module, parent_stmt_to_comprehensions).run()
