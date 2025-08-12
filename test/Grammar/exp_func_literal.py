from .assertion_utils import assert_ast_equals, show_token

func_literal_exp_code = """
f = (x) => x + 1;
"""
func_literal_exp_result = """
f = temp
"""


def test_exp_func_literal_exp():
    show_token(func_literal_exp_code)
    assert_ast_equals(func_literal_exp_code, func_literal_exp_result)


func_literal_exp_typed_code = """
f = (x: int) -> int => x + 1;
"""
func_literal_exp_typed_result = """
f = temp
"""
# TODO: Temporal


def test_exp_func_literal_exp_typed():
    assert_ast_equals(func_literal_exp_typed_code, func_literal_exp_typed_result)


func_literal_block_code = """
(x) => {
    return x + 1;
};
"""
func_literal_block_result = """
temp
"""
# TODO: Temporal


def test_exp_func_literal_block_():
    assert_ast_equals(func_literal_block_code, func_literal_block_result)


func_literal_block_typed_code = """
f = (x: int) -> int => {
    return x + 1;
};
"""
func_literal_block_typed_result = """
f = temp
"""
# TODO: Temporal


def test_exp_func_literal_block_typed():
    assert_ast_equals(func_literal_block_typed_code, func_literal_block_typed_result)
