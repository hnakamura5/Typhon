from ..assertion_utils import assert_ast_equals
from ...src.Grammar.typhon_ast import (
    is_var_assign,
    is_let_assign,
    is_decl_assign,
)
import ast


def assert_not_decl_assign(node: ast.AST):
    assert not is_decl_assign(node)
    assert not is_var_assign(node)
    assert not is_let_assign(node)


def assert_is_var(node: ast.AST):
    assert is_decl_assign(node)
    assert is_var_assign(node)
    assert not is_let_assign(node)


def assert_is_let(node: ast.AST):
    assert is_decl_assign(node)
    assert is_let_assign(node)
    assert not is_var_assign(node)


assign_code = """
x = 1;
"""
assign_result = """
x = 1
"""


def test_stmt_assign():
    parsed = assert_ast_equals(assign_code, assign_result)
    assert_not_decl_assign(parsed.body[0])


assign_code_type_annotation = """
x: int = 1;
"""
assign_result_type_annotation = """
x: int = 1
"""


def test_stmt_assign_type_annotation():
    parsed = assert_ast_equals(
        assign_code_type_annotation, assign_result_type_annotation
    )
    assert_not_decl_assign(parsed.body[0])


assign_code_var = """
var x = 1;
"""

assign_result_var = """
x = 1
"""


def test_stmt_assign_var():
    parsed = assert_ast_equals(assign_code_var, assign_result_var)
    assert_is_var(parsed.body[0])


assign_code_var_type_annotation = """
var x: int = 1;
"""
assign_result_var_type_annotation = """
x: int = 1
"""


def test_stmt_assign_var_type_annotation():
    parsed = assert_ast_equals(
        assign_code_var_type_annotation, assign_result_var_type_annotation
    )
    assert_is_var(parsed.body[0])


assign_code_let = """
let x = 1;
"""
assign_result_let = """
x = 1
"""


def test_stmt_assign_let():
    parsed = assert_ast_equals(assign_code_let, assign_result_let)
    assert_is_let(parsed.body[0])


assign_code_let_type_annotation = """
let x: int = 1;
"""
assign_result_let_type_annotation = """
x: int = 1
"""


def test_stmt_assign_let_type_annotation():
    parsed = assert_ast_equals(
        assign_code_let_type_annotation, assign_result_let_type_annotation
    )
    assert_is_let(parsed.body[0])


assign_code_var_multiple = """
var x = 1, y = 2;
"""
assign_result_var_multiple = """
x = 1
y = 2
"""


def test_stmt_assign_var_multiple():
    parsed = assert_ast_equals(assign_code_var_multiple, assign_result_var_multiple)
    assert_is_var(parsed.body[0])
    assert_is_var(parsed.body[1])


assign_code_var_type_annotation_multiple = """
var x: int = 1, y: int = 2;
"""
assign_result_var_type_annotation_multiple = """
x: int = 1
y: int = 2
"""


def test_stmt_assign_var_type_annotation_multiple():
    parsed = assert_ast_equals(
        assign_code_var_type_annotation_multiple,
        assign_result_var_type_annotation_multiple,
    )
    assert_is_var(parsed.body[0])
    assert_is_var(parsed.body[1])


assign_code_let_multiple = """
let x = 1, y = 2;
"""
assign_result_let_multiple = """
x = 1
y = 2
"""


def test_stmt_assign_let_multiple():
    parsed = assert_ast_equals(assign_code_let_multiple, assign_result_let_multiple)
    assert_is_let(parsed.body[0])
    assert_is_let(parsed.body[1])


assign_code_let_type_annotation_multiple = """
let x: int = 1, y: int = 2;
"""
assign_result_let_type_annotation_multiple = """
x: int = 1
y: int = 2
"""


def test_stmt_assign_let_type_annotation_multiple():
    parsed = assert_ast_equals(
        assign_code_let_type_annotation_multiple,
        assign_result_let_type_annotation_multiple,
    )
    assert_is_let(parsed.body[0])
    assert_is_let(parsed.body[1])


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
