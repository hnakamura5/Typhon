from ..assertion_utils import assert_transform, assert_transform_first_error


block_while_code = """
var x = 10;
while (x > 0) {
    print(x);
    var x = x - 1;
    print(x);
    x = x - 2;
}
"""

block_while_result = """
x = 10
while x > 0:
    print(x)
    _typh_vr_m0_0_x = x - 1
    print(_typh_vr_m0_0_x)
    _typh_vr_m0_0_x = _typh_vr_m0_0_x - 2
"""


def test_block_while():
    assert_transform(block_while_code, block_while_result)
