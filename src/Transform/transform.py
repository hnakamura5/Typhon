import ast
from .func_literal_to_def import func_literal_to_def
from .func_type_to_protocol import func_type_to_protocol
from .scope_check_rename import scope_check_rename
from .forbidden_statements import check_forbidden_statements
from .insert_self_to_method import insert_self_to_method
from .type_annotation_check_expand import type_annotation_check_expand


def transform(mod: ast.Module):
    check_forbidden_statements(mod)
    insert_self_to_method(mod)
    print(f"After insert_self_to_method:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    func_literal_to_def(mod)
    print(f"After func_literal_to_def:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    func_type_to_protocol(mod)
    print(f"After func_type_to_protocol:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    scope_check_rename(mod)
    print(f"After scope_check_rename:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    type_annotation_check_expand(mod)
    print(
        f"After type_annotation_check_expand:\n{ast.unparse(mod)}\n"
    )  # [HN] For debug.
