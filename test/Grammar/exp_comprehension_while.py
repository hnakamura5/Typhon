from ..assertion_utils import assert_ast_equals, assert_transform_equals


code_while_comp = """
let inf = (while (True) yield 1);
"""
result_while_comp = """
inf = __while_comp
"""
transformed_while_comp = """
def _typh_cc_m0_0():
    while True:
        yield 1
inf = _typh_cc_m0_0()
"""


def test_while_comp():
    parsed = assert_ast_equals(code_while_comp, result_while_comp)
    assert_transform_equals(parsed, transformed_while_comp)
