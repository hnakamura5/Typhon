import ast
from .func_literal_to_def import func_literal_to_def


def transform(mod: ast.Module):
    func_literal_to_def(mod)
