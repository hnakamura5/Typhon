from .assertion_utils import assert_ast_equals


code_with = """
with (f = open(name)) {
    line = f.readline();
}
"""
result_with = """
with open(name) as f:
    line = f.readline()
"""


def test_stmt_with():
    assert_ast_equals(code_with, result_with)
