import ast
from .func_literal_to_def import func_literal_to_def
from .func_type_to_protocol import func_type_to_protocol


def transform(mod: ast.Module):
    func_literal_to_def(mod)
    func_type_to_protocol(mod)
