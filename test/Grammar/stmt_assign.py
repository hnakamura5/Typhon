from ..assertion_utils import (
    assert_ast_equals,
    assert_ast_transform,
    assert_transform_error,
)
from ...src.Grammar.typhon_ast import (
    is_var_assign,
    is_let_assign,
    is_decl_assign,
)
from ...src.Grammar.syntax_errors import TypeAnnotationError
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


decl_assign_unpack_tuple_code = """
let (a, b, c) = (1, 2, 'str');
"""
decl_assign_unpack_tuple_result = """
a, b, c = (1, 2, 'str')
"""


def test_decl_assign_unpack_tuple():
    parsed = assert_ast_equals(
        decl_assign_unpack_tuple_code, decl_assign_unpack_tuple_result
    )
    assert_is_let(parsed.body[0])


decl_assign_unpack_tuple_annotation_code = """
let (a, b, c): (int, int, str) = (1, 2, 'str');
"""
decl_assign_unpack_tuple_annotation_result = """
a: int
b: int
c: str
a, b, c = (1, 2, 'str')
"""


def test_decl_assign_unpack_tuple_annotation():
    assert_ast_transform(
        decl_assign_unpack_tuple_annotation_code,
        decl_assign_unpack_tuple_annotation_result,
    )


decl_assign_unpack_annotation_each_code = """
let (a:int, b:int, c:str) = (1, 2, 'str')
"""
decl_assign_unpack_annotation_each_result = """
a: int
b: int
c: str
a, b, c = (1, 2, 'str')
"""


def test_decl_assign_unpack_tuple_annotation_each():
    assert_ast_transform(
        decl_assign_unpack_annotation_each_code,
        decl_assign_unpack_annotation_each_result,
    )


# Duplication is allowed. If contradicts each other, it becomes type error by checker.
decl_assign_unpack_annotation_both_code = """
let (a: int, b) : (int, str) = (1, '2');
"""
decl_assign_unpack_annotation_both_result = """
a: int
a: int
b: str
a, b = (1, '2')
"""


def test_decl_assign_unpack_annotation_both():
    assert_ast_transform(
        decl_assign_unpack_annotation_both_code,
        decl_assign_unpack_annotation_both_result,
    )


decl_assign_unpack_list_code = """
var [a, b, *c] = [1, 2, 3, 4];
"""
decl_assign_unpack_list_result = """
[a, b, *c] = [1, 2, 3, 4]
"""


def test_decl_assign_unpack_list():
    parsed = assert_ast_equals(
        decl_assign_unpack_list_code, decl_assign_unpack_list_result
    )
    assert_is_var(parsed.body[0])


decl_assign_unpack_list_annotation_code = """
var [a, b, *c]: list[int] = [1, 2, 3, 4];
"""
decl_assign_unpack_list_annotation_result = """
a: int
b: int
c: list[int]
[a, b, *c] = [1, 2, 3, 4]
"""


def test_decl_assign_unpack_list_annotation():
    assert_ast_transform(
        decl_assign_unpack_list_annotation_code,
        decl_assign_unpack_list_annotation_result,
    )


decl_assign_unpack_star_annotation_code = """
var [a, b:int, *c: list[int]] = [1, 2, 3, 4];
"""
decl_assign_unpack_star_annotation_result = """
b: int
c: list[int]
[a, b, *c] = [1, 2, 3, 4]
"""


def test_decl_assign_unpack_star_annotation():
    assert_ast_transform(
        decl_assign_unpack_star_annotation_code,
        decl_assign_unpack_star_annotation_result,
    )


decl_assign_unpack_annotation_error_code = """
var (a, b, c): (int, int);
"""


def test_decl_assign_unpack_annotation_error():
    assert_transform_error(
        "var (a, b, c): (int, int);",
        TypeAnnotationError,
    )
    assert_transform_error(
        "var (a, b, c): (int, int, int, int);",
        TypeAnnotationError,
    )
    assert_transform_error(
        "var [a, b, c]: list[int, str];",
        TypeAnnotationError,
    )
