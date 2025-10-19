import ast
from ..Grammar.typhon_ast import (
    is_static,
    get_pos_attributes,
    is_function_literal_def,
)
from .visitor import TyphonASTVisitor, TyphonASTTransformer


class _Gather(TyphonASTVisitor):
    methods: list[ast.FunctionDef | ast.AsyncFunctionDef]

    def __init__(self, module: ast.Module):
        super().__init__(module)
        self.methods = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        print(
            f"insert_self_to_method visit: {node} {node.__dict__} parent={self.get_parent_python_scope(ignore_top=True)}"
        )
        if (
            isinstance(self.get_parent_python_scope(ignore_top=True), ast.ClassDef)
            and not is_static(node)
            and not is_function_literal_def(node)
        ):
            self.methods.append(node)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if (
            isinstance(self.get_parent_python_scope(ignore_top=True), ast.ClassDef)
            and not is_static(node)
            and not is_function_literal_def(node)
        ):
            self.methods.append(node)
        return self.generic_visit(node)


def insert_self_to_method(mod: ast.Module):
    gather = _Gather(mod)
    gather.run()
    for method in gather.methods:
        print(f"insert_self_to_method: {method.name} {method.args}")
        new_arg = ast.arg(arg="self", annotation=None, **get_pos_attributes(method))
        method.args.args.insert(0, new_arg)
