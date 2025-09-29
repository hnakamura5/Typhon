import ast
from .func_literal_to_def import func_literal_to_def
from .type_abbrev_desugar import type_abbrev_desugar
from .scope_check_rename import scope_check_rename
from .forbidden_statements import check_forbidden_statements
from .insert_self_to_method import insert_self_to_method
from .type_annotation_check_expand import type_annotation_check_expand
from .const_member_to_final import const_member_to_final
from .inline_statement_block_capture import inline_statement_block_capture
from .optional_operators_to_checked import optional_to_checked
from .if_while_let import if_while_let_transform


def transform(mod: ast.Module):
    check_forbidden_statements(mod)
    if_while_let_transform(mod)
    print(f"After if_while_let_transform:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    insert_self_to_method(mod)
    print(f"After insert_self_to_method:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    func_literal_to_def(mod)
    print(f"After func_literal_to_def:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    type_abbrev_desugar(mod)
    print(f"After func_type_to_protocol:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    scope_check_rename(mod)
    print(f"After scope_check_rename:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    optional_to_checked(mod)
    print(f"After optional_to_checked:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    type_annotation_check_expand(mod)
    print(
        f"After type_annotation_check_expand:\n{ast.unparse(mod)}\n"
    )  # [HN] For debug.
    const_member_to_final(mod)
    print(f"After const_member_to_property:\n{ast.unparse(mod)}\n")  # [HN] For debug.
    inline_statement_block_capture(mod)
    print(
        f"After inline_statement_block_capture:\n{ast.unparse(mod)}\n"
    )  # [HN] For debug.
