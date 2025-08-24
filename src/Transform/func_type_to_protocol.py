import ast
from ..Grammar.typhon_ast import FunctionType
from .visitor import TyphonASTVisitor


class _Gather(TyphonASTVisitor):
    func_types: list[tuple[FunctionType, ast.stmt]]

    def __init__(self):
        super().__init__()
        self.func_types = []

    def visit_FunctionType(self, node: FunctionType):
        self.func_types.append((node, self.parent_stmts[-1]))
        return super().visit_FunctionType(node)


def func_type_to_protocol(mod: ast.Module):
    gatherer = _Gather()
    gatherer.visit(mod)
    for func_type, parent_stmt in gatherer.func_types:
        pass
