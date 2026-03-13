from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

func_literal_exp_code = """
var f = (x) => x + 1;
"""
func_literal_exp_result = """
f = lambda x: x + 1
"""
func_literal_exp_transformed = """
f = lambda x: x + 1
"""


def test_exp_func_literal_exp():
    parsed = assert_parse(func_literal_exp_code, func_literal_exp_result)
    assert_transform_ast(parsed, func_literal_exp_transformed)
    assert_typh_code_match_unparse(func_literal_exp_code)


func_literal_exp_typed_code = """
var f = (x: int) -> int => x + 1;
"""
func_literal_exp_typed_result = """
f = __function_literal
"""
func_literal_exp_typed_transformed = """
def $anonymous1(x: int) -> int:
    return x + 1
f = $anonymous1
"""


def test_exp_func_literal_exp_typed():
    parsed = assert_parse(func_literal_exp_typed_code, func_literal_exp_typed_result)
    assert_transform_ast(parsed, func_literal_exp_typed_transformed)
    assert_typh_code_match_unparse(func_literal_exp_typed_code)


func_literal_block_code = """
(x) => {
    return x + 1;
};
"""
func_literal_block_result = """
__function_literal
"""
func_literal_block_transformed = """
def $anonymous1(x):
    return x + 1
$anonymous1
"""


def test_exp_func_literal_block_():
    parsed = assert_parse(func_literal_block_code, func_literal_block_result)
    assert_transform_ast(parsed, func_literal_block_transformed)
    assert_typh_code_match_unparse(func_literal_block_code)


func_literal_block_typed_code = """
var f = (x: int) -> int => {
    return x + 1;
};
"""
func_literal_block_typed_result = """
f = __function_literal
"""
func_literal_block_typed_transformed = """
def $anonymous1(x: int) -> int:
    return x + 1
f = $anonymous1
"""


def test_exp_func_literal_block_typed():
    parsed = assert_parse(
        func_literal_block_typed_code, func_literal_block_typed_result
    )
    assert_transform_ast(parsed, func_literal_block_typed_transformed)
    assert_typh_code_match_unparse(func_literal_block_typed_code)


func_literal_nested_code = """
def test_exp_func_literal_nested() {
    var f = (x: int) -> (int) -> int => {
        if (x > 0) {
            return (x: int) -> int => {
                return x + 1;
            };
        } else {
            return (x: int) -> int => {
                return x - 1;
            };
        }
    };
    var g = (x: int) -> int => {
        return x * 2;
    };
}
"""
func_literal_nested_result = """
def test_exp_func_literal_nested():
    f = __function_literal
    g = __function_literal
"""
func_literal_nested_transformed = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0: int, /) -> int:
        ...

def test_exp_func_literal_nested():

    def $anonymous2(x: int) -> $func_type1:
        if x > 0:

            def $anonymous3(x: int) -> int:
                return x + 1
            return $anonymous3
        else:

            def $anonymous4(x: int) -> int:
                return x - 1
            return $anonymous4
    f = $anonymous2

    def $anonymous5(x: int) -> int:
        return x * 2
    g = $anonymous5
"""


def test_exp_func_literal_nested():
    parsed = assert_parse(func_literal_nested_code, func_literal_nested_result)
    assert_transform_ast(parsed, func_literal_nested_transformed)
    assert_typh_code_match_unparse(func_literal_nested_code)
