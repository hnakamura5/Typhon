import ast
from ...src.Grammar.parser import parse_string

assign_code = """
x = 1;
"""
assign_result = """
x = 1
"""


def test_stmt_assign():
    parsed = parse_string(assign_code, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == assign_result.strip()


assign_code_type_annotation = """
x: int = 1;
"""
assign_result_type_annotation = """
x: int = 1
"""


def test_stmt_assign_type_annotation():
    parsed = parse_string(assign_code_type_annotation, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == assign_result_type_annotation.strip()


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
    parsed = parse_string(code_stmt_assign_in_func, mode="exec", verbose=True)
    assert isinstance(parsed, ast.Module)
    assert ast.unparse(parsed) == result_stmt_assign_in_func.strip()
