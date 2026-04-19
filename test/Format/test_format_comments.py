import ast

from Typhon.Format.attach_comments import attach_comments, attach_comments_v2
from Typhon.Format.doc_render import render_doc_to_string
from Typhon.Format.print_to_doc import print_to_doc
from Typhon.Grammar.parser import parse_string
from Typhon.SourceMap.source_ast_cache import SourceAstCache


def _format(source: str) -> str:
    module = parse_string(source, mode="exec")
    assert isinstance(module, ast.Module)
    # attach_comments(module)
    attach_comments_v2(
        module,
        SourceAstCache(module, source, "<string>"),
    )
    return render_doc_to_string(print_to_doc(module))


def _assert_format(source: str, expected: str) -> None:
    result = _format(source)
    assert result == expected.strip(), (
        f"Expected:\n{expected.strip()}\n\nGot:\n{result}"
    )
    # Round-trip: formatting the output again should be stable
    round_tripped = _format(result)
    assert round_tripped.strip() == expected.strip(), (
        f"Round trip failed.\nExpected:\n{expected.strip()}\n\nGot:\n{round_tripped}"
    )


# ---------------------------------------------------------------------------
# Leading comments
# ---------------------------------------------------------------------------


code_leading_comment_before_stmt = """
# header
let x = 1
"""
result_leading_comment_before_stmt = """
# header
let x = 1
"""


def test_leading_comment_before_stmt():
    _assert_format(code_leading_comment_before_stmt, result_leading_comment_before_stmt)


code_leading_comment_between_stmts = """
let x = 1
# middle
let y = 2
"""
result_leading_comment_between_stmts = """
let x = 1
# middle
let y = 2
"""


def test_leading_comment_between_stmts():
    _assert_format(
        code_leading_comment_between_stmts, result_leading_comment_between_stmts
    )


code_multiple_leading_comments = """
# first
# second
let x = 1
"""
result_multiple_leading_comments = """
# first
# second
let x = 1
"""


def test_multiple_leading_comments():
    _assert_format(code_multiple_leading_comments, result_multiple_leading_comments)


# ---------------------------------------------------------------------------
# Trailing comments
# ---------------------------------------------------------------------------


code_trailing_comment_on_stmt = """
let x = 1  # note
"""
result_trailing_comment_on_stmt = """
let x = 1  # note
"""


def test_trailing_comment_on_stmt():
    _assert_format(code_trailing_comment_on_stmt, result_trailing_comment_on_stmt)


code_trailing_comment_on_first_of_two_stmts = """
let x = 1  # note
let y = 2
"""
result_trailing_comment_on_first_of_two_stmts = """
let x = 1  # note
let y = 2
"""


def test_trailing_comment_on_first_of_two_stmts():
    _assert_format(
        code_trailing_comment_on_first_of_two_stmts,
        result_trailing_comment_on_first_of_two_stmts,
    )


# ---------------------------------------------------------------------------
# Leading + trailing mixed
# ---------------------------------------------------------------------------


code_leading_and_trailing_on_same_stmt = """
# before
let x = 1  # after
"""
result_leading_and_trailing_on_same_stmt = """
# before
let x = 1  # after
"""


def test_leading_and_trailing_on_same_stmt():
    _assert_format(
        code_leading_and_trailing_on_same_stmt,
        result_leading_and_trailing_on_same_stmt,
    )


# ---------------------------------------------------------------------------
# Comments inside function body
# ---------------------------------------------------------------------------


code_leading_comment_inside_function = """
def f() {
    # body comment
    let x = 1
}
"""
result_leading_comment_inside_function = """
def f() {
    # body comment
    let x = 1
}
"""


def test_leading_comment_inside_function():
    _assert_format(
        code_leading_comment_inside_function,
        result_leading_comment_inside_function,
    )


code_trailing_comment_inside_function = """
def f() {
    let x = 1  # note
}
"""
result_trailing_comment_inside_function = """
def f() {
    let x = 1  # note
}
"""


def test_trailing_comment_inside_function():
    _assert_format(
        code_trailing_comment_inside_function,
        result_trailing_comment_inside_function,
    )


# ---------------------------------------------------------------------------
# Dangling comments
# ---------------------------------------------------------------------------


code_dangling_comment_in_empty_function = """
def f() {
    # todo
}
"""
result_dangling_comment_in_empty_function = """
def f() {
    # todo
}
"""


def test_dangling_comment_in_empty_function():
    _assert_format(
        code_dangling_comment_in_empty_function,
        result_dangling_comment_in_empty_function,
    )


code_dangling_comment_in_module_only = """
# only comment
"""
result_dangling_comment_in_module_only = """
# only comment
"""


def test_dangling_comment_in_module_only():
    _assert_format(
        code_dangling_comment_in_module_only,
        result_dangling_comment_in_module_only,
    )


# ---------------------------------------------------------------------------
# Block comments
# ---------------------------------------------------------------------------


code_block_comment_leading = """
#( block )#
let x = 1
"""
result_block_comment_leading = """
#( block )#
let x = 1
"""


def test_block_comment_leading():
    _assert_format(code_block_comment_leading, result_block_comment_leading)


# ---------------------------------------------------------------------------
# Expression-level inline comments
# ---------------------------------------------------------------------------


code_expression_trailing_comment_on_call = """
let x = f(
    a,  # first
    #(second)# b
)
"""
result_expression_trailing_comment_on_call = """
let x = f(
    a,  # first
    #(second)# b,
)
"""


def test_expression_trailing_comment_on_call():
    # Comment on an argument forces the call to stay multi-line
    _assert_format(
        code_expression_trailing_comment_on_call,
        result_expression_trailing_comment_on_call,
    )


code_expression_trailing_comment_stays_on_multiline_call = """
let x = f(
    very_long_argument_name,  # note
    another_very_long_argument_name
)
"""
result_expression_trailing_comment_stays_on_multiline_call = """
let x = f(
    very_long_argument_name,  # note
    another_very_long_argument_name,
)
"""


def test_expression_trailing_comment_stays_on_multiline_call():
    _assert_format(
        code_expression_trailing_comment_stays_on_multiline_call,
        result_expression_trailing_comment_stays_on_multiline_call,
    )


code_trailing_comment_at_end = """
let x = 1
# end
"""
result_trailing_comment_at_end = """
let x = 1
# end
"""


def test_trailing_comment_at_end():
    _assert_format(code_trailing_comment_at_end, result_trailing_comment_at_end)


# ---------------------------------------------------------------------------
# Comments on definition statements (function/class)
# ---------------------------------------------------------------------------


code_leading_comment_before_function_def = """
# function note
def f() {
    pass
}
"""
result_leading_comment_before_function_def = """
# function note
def f() { pass }
"""


def test_leading_comment_before_function_def():
    _assert_format(
        code_leading_comment_before_function_def,
        result_leading_comment_before_function_def,
    )


code_trailing_comment_on_function_def = """
def f() {  # function trailing
    pass
}
"""
result_trailing_comment_on_function_def = """
def f() {
    # function trailing
    pass
}
"""


def test_trailing_comment_on_function_def():
    _assert_format(
        code_trailing_comment_on_function_def,
        result_trailing_comment_on_function_def,
    )


code_leading_comment_before_class_def = """
# class note
class C {
    pass
}
"""
result_leading_comment_before_class_def = """
# class note
class C { pass }
"""


def test_leading_comment_before_class_def():
    _assert_format(
        code_leading_comment_before_class_def,
        result_leading_comment_before_class_def,
    )


code_trailing_comment_on_class_def = """
class C {  # class trailing
    pass
}
"""
result_trailing_comment_on_class_def = """
class C {
    # class trailing
    pass
}
"""


def test_trailing_comment_on_class_def():
    _assert_format(
        code_trailing_comment_on_class_def,
        result_trailing_comment_on_class_def,
    )


# ---------------------------------------------------------------------------
# Comments around bases/parameters/type parameters
# ---------------------------------------------------------------------------


code_class_bases_with_comments = """
class C(
    BaseA,  # base a
    #(base b)# BaseB,
) {
    pass
}
"""
result_class_bases_with_comments = """
class C(
    BaseA,  # base a
    #(base b)# BaseB,
) { pass }
"""


def test_class_bases_with_comments():
    _assert_format(
        code_class_bases_with_comments,
        result_class_bases_with_comments,
    )


code_function_params_with_comments = """
def f(
    a,  # first
    #(second)# b,
) {
    pass
}
"""
result_function_params_with_comments = """
def f(
    a,  # first
    #(second)# b
) { pass }
"""


def test_function_params_with_comments():
    _assert_format(
        code_function_params_with_comments,
        result_function_params_with_comments,
    )


code_class_type_params_with_comments = """
class Box[
    T,  # type t
    #(type u)# U,
] {
    pass
}
"""
result_class_type_params_with_comments = """
class Box[
    T,  # type t
    #(type u)# U,
] { pass }
"""


def test_class_type_params_with_comments():
    _assert_format(
        code_class_type_params_with_comments,
        result_class_type_params_with_comments,
    )


code_function_type_params_and_params_with_comments = """
def g[
    T,  # type t
    #(type u)# U,
](
    x,  # arg x
    #(arg y)# y,
) {
    pass
}
"""
result_function_type_params_and_params_with_comments = """
def g[
    T,  # type t
    #(type u)# U,
](
    x,  # arg x
    #(arg y)# y
) { pass }
"""


def test_function_type_params_and_params_with_comments():
    _assert_format(
        code_function_type_params_and_params_with_comments,
        result_function_type_params_and_params_with_comments,
    )
