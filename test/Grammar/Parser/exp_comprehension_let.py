from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_typh_code_match_unparse,
)

comp_let_code = """
let val = (let x = 3; x * x);
"""
comp_let_result = """
val = __let_comp
"""
comp_let_transformed = """
def _typh_cc_m0_0():
    x = 3
    return x * x
val = _typh_cc_m0_0()
"""


def test_comp_let():
    parsed = assert_ast_equals(comp_let_code, comp_let_result)
    assert_transform_equals(parsed, comp_let_transformed)
    assert_typh_code_match_unparse(comp_let_code)


comp_let_multi_code = """
let val = (let x = 3, y = 4; x + y);
"""
comp_let_multi_result = """
val = __let_comp
"""
comp_let_multi_transformed = """
def _typh_cc_m0_0():
    x = 3
    y = 4
    return x + y
val = _typh_cc_m0_0()
"""


def test_comp_let_multi():
    parsed = assert_ast_equals(comp_let_multi_code, comp_let_multi_result)
    assert_transform_equals(parsed, comp_let_multi_transformed)
    assert_typh_code_match_unparse(comp_let_multi_code)
