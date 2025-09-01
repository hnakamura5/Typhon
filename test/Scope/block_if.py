from ..assertion_utils import assert_ast_transform

block_if_code = """
var x = 10;
if (x > 5) {
    print(x);
    var x = 20;
    print(x + 1);
    x = 30
} else {
    var x = 5;
    print(x);
    x = 40
}
"""
block_if_result = """
x = 10
if x > 5:
    print(x)
    _typh_vr_m0_0_x = 20
    print(_typh_vr_m0_0_x + 1)
    _typh_vr_m0_0_x = 30
else:
    _typh_vr_m0_1_x = 5
    print(_typh_vr_m0_1_x)
    _typh_vr_m0_1_x = 40
"""


def test_block_if():
    assert_ast_transform(block_if_code, block_if_result)


block_if_nested_code = """
var x = 10;
if (x >= 10) {
    print(x);
    var x = 20;
    if (x <= 20) {
        print(x);
        x = 15;
        var x = 5;
        print(x);
    }
}
"""
block_if_nested_result = """
x = 10
if x >= 10:
    print(x)
    _typh_vr_m0_0_x = 20
    if _typh_vr_m0_0_x <= 20:
        print(_typh_vr_m0_0_x)
        _typh_vr_m0_0_x = 15
        _typh_vr_m0_1_x = 5
        print(_typh_vr_m0_1_x)
"""


def test_block_if_nested():
    assert_ast_transform(block_if_nested_code, block_if_nested_result)
