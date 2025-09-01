from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Grammar.syntax_errors import ScopeError

block_match_code = """
let x = 10;
match (x) {
    case (x, y) if (x > 5) {
        print(x);
        var x = 20;
        x = x + y;
        print(x);
    }
    case (y, *x) if (len(x) > 2) {
        print(x);
        var x = 5;
        print(x);
        x = x * 2;
    }
    case(x) {
        print(x);
        let x = 100;
        print(x);
    }
    case(_) {
        print(x);
        let x = 100;
        print(x);
    }
}
print(x);
"""

block_match_result = """
x = 10
match x:
    case [_typh_vr_m0_0_x, y] if _typh_vr_m0_0_x > 5:
        print(_typh_vr_m0_0_x)
        _typh_vr_m0_1_x = 20
        _typh_vr_m0_1_x = _typh_vr_m0_1_x + y
        print(_typh_vr_m0_1_x)
    case [y, *_typh_vr_m0_2_x] if len(_typh_vr_m0_2_x) > 2:
        print(_typh_vr_m0_2_x)
        _typh_vr_m0_3_x = 5
        print(_typh_vr_m0_3_x)
        _typh_vr_m0_3_x = _typh_vr_m0_3_x * 2
    case _typh_vr_m0_4_x:
        print(_typh_vr_m0_4_x)
        _typh_vr_m0_5_x = 100
        print(_typh_vr_m0_5_x)
    case _:
        print(x)
        _typh_vr_m0_6_x = 100
        print(_typh_vr_m0_6_x)
print(x)
"""


def test_block_match():
    assert_ast_transform(block_match_code, block_match_result)
