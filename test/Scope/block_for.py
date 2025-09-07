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


for_unpack_typed_code = """
for (var (a, b): (int, float) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
for_unpack_typed_result = """
_typh_vr_m0_0_a: int
_typh_vr_m0_1_b: float
for _typh_vr_m0_0_a, _typh_vr_m0_1_b in [(1, 1.0), (2, 2.0)]:
    print(_typh_vr_m0_0_a)
    print(_typh_vr_m0_1_b)
"""


def test_stmt_for_unpack_typed():
    assert_ast_transform(for_unpack_typed_code, for_unpack_typed_result)
