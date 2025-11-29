import ast
from ..Driver.debugging import debug_print, debug_verbose_print
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
from .comprehension_to_function import comprehension_to_function
from .placeholder_to_function import placeholder_to_func
from .record_to_dataclass import record_to_dataclass
from .extended_patterns import extended_protocol

from ..Grammar.syntax_errors import raise_from_module_syntax_errors


def transform(mod: ast.Module):
    check_forbidden_statements(mod)
    record_to_dataclass(mod)
    debug_verbose_print(f"After record_to_dataclass:\n{ast.unparse(mod)}\n")
    extended_protocol(mod)
    debug_verbose_print(f"After extended_protocol:\n{ast.unparse(mod)}\n")
    inline_statement_block_capture(mod)
    debug_print(f"After inline_statement_block_capture:\n{ast.unparse(mod)}\n")
    if_while_let_transform(mod)
    debug_verbose_print(f"After if_while_let_transform:\n{ast.unparse(mod)}\n")
    insert_self_to_method(mod)
    debug_verbose_print(f"After insert_self_to_method:\n{ast.unparse(mod)}\n")
    comprehension_to_function(mod)
    debug_verbose_print(f"After comprehension_to_function:\n{ast.unparse(mod)}\n")
    func_literal_to_def(mod)
    debug_print(f"After func_literal_to_def:\n{ast.unparse(mod)}\n")
    scope_check_rename(mod)
    debug_print(f"After scope_check_rename:\n{ast.unparse(mod)}\n")
    placeholder_to_func(mod)
    debug_print(f"After placeholder_to_func:\n{ast.unparse(mod)}\n")
    optional_to_checked(mod)
    debug_verbose_print(f"After optional_to_checked:\n{ast.unparse(mod)}\n")
    type_annotation_check_expand(mod)
    debug_verbose_print(f"After type_annotation_check_expand:\n{ast.unparse(mod)}\n")
    type_abbrev_desugar(mod)
    debug_verbose_print(f"After func_type_to_protocol:\n{ast.unparse(mod)}\n")
    const_member_to_final(mod)
    debug_print(f"After transform:\n{ast.unparse(mod)}\n")
    raise_from_module_syntax_errors(mod)
