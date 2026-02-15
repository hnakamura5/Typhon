from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_transform_first_error,
    assert_typh_code_match_unparse,
)
from Typhon.Grammar.syntax_errors import TypeAnnotationError
from Typhon.Driver.debugging import set_debug_first_error


tuple_type_code = """
var t: (int, str) = (1, "a");
"""
tuple_type_result = """
t: (int, str) = (1, 'a')
"""
tuple_type_transformed = """
t: tuple[int, str] = (1, 'a')
"""


def test_exp_tuple_type():
    parsed = assert_parse(tuple_type_code, tuple_type_result)
    assert_transform_ast(parsed, tuple_type_transformed)
    assert_typh_code_match_unparse(tuple_type_code)


list_type_code = """
var l: [int] = [1, 2, 3];
"""
list_type_result = """
l: [int] = [1, 2, 3]
"""
list_type_transformed = """
l: list[int] = [1, 2, 3]
"""


def test_exp_list_type():
    parsed = assert_parse(list_type_code, list_type_result)
    assert_transform_ast(parsed, list_type_transformed)
    assert_typh_code_match_unparse(list_type_code)


list_type_nested_code = """
var l: [[int]] = [[1, 2], [3, 4]];
"""
list_type_nested_result = """
l: [[int]] = [[1, 2], [3, 4]]
"""
list_type_nested_transformed = """
l: list[list[int]] = [[1, 2], [3, 4]]
"""


def test_exp_list_type_nested():
    parsed = assert_parse(list_type_nested_code, list_type_nested_result)
    assert_transform_ast(parsed, list_type_nested_transformed)
    assert_typh_code_match_unparse(list_type_nested_code)


list_type_error_code = """
var l: [int, int] = [1, 2];
"""


def test_exp_list_type_error():
    assert_transform_first_error(
        list_type_error_code,
        exception=TypeAnnotationError,
    )


tuple_list_type_nested_code = """
var x: (int, [str], (int, int)) = (1, ["a", "b"], (2, 3));
"""
tuple_list_type_nested_result = """
x: (int, [str], (int, int)) = (1, ['a', 'b'], (2, 3))
"""
tuple_list_type_nested_transformed = """
x: tuple[int, list[str], tuple[int, int]] = (1, ['a', 'b'], (2, 3))
"""


def test_exp_tuple_list_type_nested():
    parsed = assert_parse(tuple_list_type_nested_code, tuple_list_type_nested_result)
    assert_transform_ast(parsed, tuple_list_type_nested_transformed)
    assert_typh_code_match_unparse(tuple_list_type_nested_code)
