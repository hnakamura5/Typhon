import ast
from ..Grammar.typhon_ast import (
    FunctionLiteral,
    get_function_literal_def,
    clear_function_literal_def,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer, flat_append


class _Gather(TyphonASTVisitor):
    func_literals: list[tuple[FunctionLiteral, ast.stmt]]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.func_literals = []

    def visit_FunctionLiteral(self, node: FunctionLiteral):
        print(f"func_literal_to_def _Gather visit: {node} {node.__dict__}")
        self.func_literals.append((node, self.parent_stmts[-1]))
        return self.generic_visit(node)


class _Transform(TyphonASTTransformer):
    func_literals: dict[FunctionLiteral, ast.stmt]
    parent_stmts_for_literals: dict[ast.stmt, list[FunctionLiteral]]

    def __init__(
        self,
        module: ast.Module,
        func_literals: dict[FunctionLiteral, ast.stmt],
        parent_stmts_for_literals: dict[ast.stmt, list[FunctionLiteral]],
    ):
        super().__init__(module)
        self.func_literals = func_literals
        self.parent_stmts_for_literals = parent_stmts_for_literals

    def visit(self, node: ast.AST):
        if not isinstance(node, ast.stmt):
            return super().visit(node)
        result: list[ast.AST] = []
        print(f"func_literal_to_def _Transform visit: {node} {node.__dict__}")
        # Expand the def of function literals before the parent statement.
        if node in self.parent_stmts_for_literals:
            for func_literal in self.parent_stmts_for_literals[node]:
                func_def = get_function_literal_def(func_literal)
                func_def.name = self.new_func_literal_name()
                func_literal.id = func_def.name
                flat_append(result, self.visit(func_def))
                clear_function_literal_def(func_literal)
        node_result = super().visit(node)
        flat_append(result, node_result)
        return result


# Entry point for the transformation.
def func_literal_to_def(mod: ast.Module):
    gatherer = _Gather(mod)
    # First, gather all function literals with their parent statements.
    gatherer.run()
    # Do transform to the literals and the parent statements.
    func_literals = {}
    parent_stmts_for_literals = {}
    for func_literal, parent_stmt in gatherer.func_literals:
        func_literals[func_literal] = parent_stmt
        parent_stmts_for_literals.setdefault(parent_stmt, []).append(func_literal)
    transformer = _Transform(
        mod,
        func_literals,
        parent_stmts_for_literals,
    )
    transformer.run()
