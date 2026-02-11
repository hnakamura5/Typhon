from ..assertion_utils import assert_transform, assert_transform_first_error
from src.Typhon.Grammar.syntax_errors import ScopeError

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
from typing import Final as _typh_bi_Final
x: _typh_bi_Final = 10
match x:
    case tuple([_typh_cn_m0_0_x, _typh_cn_m0_1_y]) if _typh_cn_m0_0_x > 5:
        _typh_cn_m0_0_x: _typh_bi_Final
        _typh_cn_m0_1_y: _typh_bi_Final
        print(_typh_cn_m0_0_x)
        _typh_vr_m0_2_x = 20
        _typh_vr_m0_2_x = _typh_vr_m0_2_x + _typh_cn_m0_1_y
        print(_typh_vr_m0_2_x)
    case tuple([_typh_cn_m0_3_y, *_typh_cn_m0_4_x]) if len(_typh_cn_m0_4_x) > 2:
        _typh_cn_m0_3_y: _typh_bi_Final
        _typh_cn_m0_4_x: _typh_bi_Final
        print(_typh_cn_m0_4_x)
        _typh_vr_m0_5_x = 5
        print(_typh_vr_m0_5_x)
        _typh_vr_m0_5_x = _typh_vr_m0_5_x * 2
    case _typh_cn_m0_6_x:
        _typh_cn_m0_6_x: _typh_bi_Final
        print(_typh_cn_m0_6_x)
        _typh_cn_m0_7_x: _typh_bi_Final = 100
        print(_typh_cn_m0_7_x)
    case _:
        print(x)
        _typh_cn_m0_8_x: _typh_bi_Final = 100
        print(_typh_cn_m0_8_x)
print(x)
"""


def test_block_match():
    assert_transform(block_match_code, block_match_result)
