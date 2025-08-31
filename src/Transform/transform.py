import ast
from .func_literal_to_def import func_literal_to_def
from .func_type_to_protocol import func_type_to_protocol
from .scope_check_rename import scope_check_rename


def transform(mod: ast.Module):
    func_literal_to_def(mod)
    print(f"After func_literal_to_def:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    func_type_to_protocol(mod)
    print(f"After func_type_to_protocol:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    scope_check_rename(mod)
