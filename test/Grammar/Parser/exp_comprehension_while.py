from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)


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
    parsed = assert_parse(code_while_comp, result_while_comp)
    assert_transform_ast(parsed, transformed_while_comp)
    assert_typh_code_match_unparse(code_while_comp)


code_while_let_comp = """
let parsed = (with (let f = open("file.txt"))
                (while (let [x, y] = f.readline().split())
                    yield (x, y)))
"""
result_while_let_comp = """
parsed = __with_control
"""
transformed_while_let_comp = """
def _typh_cc_m0_0():
    with open('file.txt') as f:

        def _typh_cc_f1_0():
            _typh_vr_f2_0_ = True
            while _typh_vr_f2_0_:
                _typh_vr_f2_0_ = False
                match f.readline().split():
                    case [x, y]:
                        yield (x, y)
                        _typh_vr_f2_0_ = True
                    case _:
                        pass
        return _typh_cc_f1_0()
parsed = _typh_cc_m0_0()
"""


def test_while_let_comp():
    parsed = assert_parse(code_while_let_comp, result_while_let_comp)
    assert_transform_ast(parsed, transformed_while_let_comp)
    assert_typh_code_match_unparse(code_while_let_comp)
