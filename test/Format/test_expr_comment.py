from .format_assertion_utils import assert_render_pipeline_comment_sensitive


code_leading_comment_before_stmt = """
# header
let x = 1
"""
result_leading_comment_before_stmt = """
# header
let x = 1
"""


def test_leading_comment_before_stmt():
    assert_render_pipeline_comment_sensitive(
        code_leading_comment_before_stmt, result_leading_comment_before_stmt
    )


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
    assert_render_pipeline_comment_sensitive(
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
    assert_render_pipeline_comment_sensitive(
        code_multiple_leading_comments, result_multiple_leading_comments
    )


code_trailing_comment_on_stmt = """
let x = 1  # note
"""
result_trailing_comment_on_stmt = """
let x = 1  # note
"""


def test_trailing_comment_on_stmt():
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_on_stmt, result_trailing_comment_on_stmt
    )


code_trailing_comment_on_first_of_two_stmts = """
let x = 1  # note
let y = 2
"""
result_trailing_comment_on_first_of_two_stmts = """
let x = 1  # note
let y = 2
"""


def test_trailing_comment_on_first_of_two_stmts():
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_on_first_of_two_stmts,
        result_trailing_comment_on_first_of_two_stmts,
    )


code_leading_and_trailing_on_same_stmt = """
# before
let x = 1  # after
"""
result_leading_and_trailing_on_same_stmt = """
# before
let x = 1  # after
"""


def test_leading_and_trailing_on_same_stmt():
    assert_render_pipeline_comment_sensitive(
        code_leading_and_trailing_on_same_stmt,
        result_leading_and_trailing_on_same_stmt,
    )


code_dangling_comment_in_module_only = """
# only comment
"""
result_dangling_comment_in_module_only = """
# only comment
"""


def test_dangling_comment_in_module_only():
    assert_render_pipeline_comment_sensitive(
        code_dangling_comment_in_module_only,
        result_dangling_comment_in_module_only,
    )


code_block_comment_leading = """
#( block )#
let x = 1
"""
result_block_comment_leading = """
#( block )#
let x = 1
"""


def test_block_comment_leading():
    assert_render_pipeline_comment_sensitive(
        code_block_comment_leading, result_block_comment_leading
    )


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
    assert_render_pipeline_comment_sensitive(
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
    assert_render_pipeline_comment_sensitive(
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
    assert_render_pipeline_comment_sensitive(
        code_trailing_comment_at_end, result_trailing_comment_at_end
    )


code_function_literal_params_with_comments = """
let f = (
    a: int,  # first
    #(second)# b: int,
) => a + b
"""
result_function_literal_params_with_comments = """
let f = (
    a: int,  # first
    #(second)# b: int,
) => a + b
"""


def test_function_literal_params_with_comments():
    assert_render_pipeline_comment_sensitive(
        code_function_literal_params_with_comments,
        result_function_literal_params_with_comments,
    )
