from ..assertion_utils import assert_ast_transform

block_for_code = """
var x = range(5);
for (let x in x) {
    print(x);
    var x = x + 1;
    print(x);
    x = x + 2;
}
"""
block_for_result = """
x = range(5)
for _typh_cn_m0_0_x in x:
    print(_typh_cn_m0_0_x)
    _typh_vr_m0_1_x = _typh_cn_m0_0_x + 1
    print(_typh_vr_m0_1_x)
    _typh_vr_m0_1_x = _typh_vr_m0_1_x + 2
"""


def test_block_for():
    assert_ast_transform(block_for_code, block_for_result)
