from .assertion_utils import assert_ast_equals, show_token, assert_transform_equals

func_literal_exp_code = """
f = (x) => x + 1;
"""
func_literal_exp_result = """
f = __function_literal
"""
func_literal_exp_transformed = """
def _typh_fn_m0_0(x):
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_exp():
    show_token(func_literal_exp_code)
    parsed = assert_ast_equals(func_literal_exp_code, func_literal_exp_result)
    assert_transform_equals(parsed, func_literal_exp_transformed)


func_literal_exp_typed_code = """
f = (x: int) -> int => x + 1;
"""
func_literal_exp_typed_result = """
f = __function_literal
"""
func_literal_exp_typed_transformed = """
def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_exp_typed():
    parsed = assert_ast_equals(
        func_literal_exp_typed_code, func_literal_exp_typed_result
    )
    assert_transform_equals(parsed, func_literal_exp_typed_transformed)


func_literal_block_code = """
(x) => {
    return x + 1;
};
"""
func_literal_block_result = """
__function_literal
"""
func_literal_block_transformed = """
def _typh_fn_m0_0(x):
    return x + 1
_typh_fn_m0_0
"""


def test_exp_func_literal_block_():
    parsed = assert_ast_equals(func_literal_block_code, func_literal_block_result)
    assert_transform_equals(parsed, func_literal_block_transformed)


func_literal_block_typed_code = """
f = (x: int) -> int => {
    return x + 1;
};
"""
func_literal_block_typed_result = """
f = __function_literal
"""
func_literal_block_typed_transformed = """
def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f = _typh_fn_m0_0
"""


def test_exp_func_literal_block_typed():
    parsed = assert_ast_equals(
        func_literal_block_typed_code, func_literal_block_typed_result
    )
    assert_transform_equals(parsed, func_literal_block_typed_transformed)
