from ..assertion_utils import (
    assert_parse,
    assert_transform,
    assert_transform_first_error,
    assert_parse_first_error,
    with_parser_verbose,
)
from ....src.Typhon.Grammar.typhon_ast import (
    is_var_assign,
    is_let_assign,
    is_decl_assign,
)
from ....src.Typhon.Grammar.syntax_errors import (
    TypeAnnotationError,
    LetMissingElseError,
)
import ast
from ....src.Typhon.Driver.debugging import (
    set_debug_first_error,
    set_debug_mode,
    set_debug_verbose,
)


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
    parsed = assert_parse(assign_code, assign_result)
    assert_not_decl_assign(parsed.body[0])


assign_code_type_annotation = """
x: int = 1;
"""
assign_result_type_annotation = """
x: int = 1
"""


def test_stmt_assign_type_annotation():
    parsed = assert_parse(assign_code_type_annotation, assign_result_type_annotation)
    assert_not_decl_assign(parsed.body[0])


assign_code_var = """
var x = 1;
"""

assign_result_var = """
x = 1
"""


def test_stmt_assign_var():
    parsed = assert_parse(assign_code_var, assign_result_var)
    assert_is_var(parsed.body[0])


assign_code_var_type_annotation = """
var x: int = 1;
"""
assign_result_var_type_annotation = """
x: int = 1
"""


def test_stmt_assign_var_type_annotation():
    parsed = assert_parse(
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
    parsed = assert_parse(assign_code_let, assign_result_let)
    assert_is_let(parsed.body[0])


assign_code_let_type_annotation = """
let x: int = 1;
"""
assign_result_let_type_annotation = """
x: int = 1
"""


def test_stmt_assign_let_type_annotation():
    parsed = assert_parse(
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
    parsed = assert_parse(assign_code_var_multiple, assign_result_var_multiple)
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
    parsed = assert_parse(
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
    parsed = assert_parse(assign_code_let_multiple, assign_result_let_multiple)
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
    parsed = assert_parse(
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
    with with_parser_verbose():
        assert_parse(code_stmt_assign_in_func, result_stmt_assign_in_func)


decl_assign_unpack_tuple_code = """
let (a, b, c) = (1, 2, 'str');
"""
decl_assign_unpack_tuple_result = """
if True:
    match (1, 2, 'str'):
        case [a, b, c]:
        case _:# type: ignore[all]
            raise TypeError
"""


def test_decl_assign_unpack_tuple():
    assert_parse(decl_assign_unpack_tuple_code, decl_assign_unpack_tuple_result)


decl_assign_unpack_tuple_annotation_code = """
let (a, b, c): (int, int, str) = (1, 2, 'str');
"""


def test_decl_assign_unpack_tuple_annotation():
    assert_parse_first_error(decl_assign_unpack_tuple_annotation_code, SyntaxError)


decl_assign_unpack_annotation_each_code = """
let (a:int, b:int, c:str) = (1, 2, 'str')
"""
decl_assign_unpack_annotation_each_transformed = """
a: int
b: int
c: str
match (1, 2, 'str'):
    case tuple([a, b, c]):
        pass
    case _:# type: ignore[all]
        raise TypeError
"""


def test_decl_assign_unpack_tuple_annotation_each():
    assert_transform(
        decl_assign_unpack_annotation_each_code,
        decl_assign_unpack_annotation_each_transformed,
    )


decl_assign_unpack_list_code = """
var [a, b, *c] = [1, 2, 3, 4];
"""


def test_decl_assign_unpack_list():
    assert_transform_first_error(decl_assign_unpack_list_code, LetMissingElseError)
