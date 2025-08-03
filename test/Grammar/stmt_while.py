from .assertion_utils import assert_ast_equals

code_while = """
while (i < 10) {
    i += 1;
}
"""
result_while = """
while i < 10:
    i += 1
"""


def test_stmt_while():
    assert_ast_equals(code_while, result_while)
