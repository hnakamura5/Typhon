from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

comp_let_code = """
let val = (let x = 3; x * x);
"""
comp_let_result = """
val = __let_comp
"""
comp_let_transformed = """
from typing import Final as _typh_bi_Final

def _typh_cc_m0_0():
    x: _typh_bi_Final = 3
    return x * x
val: _typh_bi_Final = _typh_cc_m0_0()
"""


def test_comp_let():
    parsed = assert_parse(comp_let_code, comp_let_result)
    assert_transform_ast(parsed, comp_let_transformed)
    assert_typh_code_match_unparse(comp_let_code)


comp_let_multi_code = """
let val = (let x = 3, y = 4; x + y);
"""
comp_let_multi_result = """
val = __let_comp
"""
comp_let_multi_transformed = """
from typing import Final as _typh_bi_Final

def _typh_cc_m0_0():
    x: _typh_bi_Final = 3
    y: _typh_bi_Final = 4
    return x + y
val: _typh_bi_Final = _typh_cc_m0_0()
"""


def test_comp_let_multi():
    parsed = assert_parse(comp_let_multi_code, comp_let_multi_result)
    assert_transform_ast(parsed, comp_let_multi_transformed)
    assert_typh_code_match_unparse(comp_let_multi_code)
