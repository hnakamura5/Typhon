from .assertion_utils import assert_ast_equals

assign_code = """
x = 1;
"""
assign_result = """
x = 1
"""


def test_stmt_assign():
    assert_ast_equals(assign_code, assign_result)


assign_code_type_annotation = """
x: int = 1;
"""
assign_result_type_annotation = """
x: int = 1
"""


def test_stmt_assign_type_annotation():
    assert_ast_equals(assign_code_type_annotation, assign_result_type_annotation)


code_stmt_assign_in_func = """
def func(x: int = 1) {
    y = x;
    return y;
}
"""
result_stmt_assign_in_func = """
def func(x: int=1):
    y = x
    return y
"""


def test_stmt_assign_in_func():
    assert_ast_equals(code_stmt_assign_in_func, result_stmt_assign_in_func)
