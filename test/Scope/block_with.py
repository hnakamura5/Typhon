from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Grammar.syntax_errors import ScopeError

block_with_code = """
let x = 10;
with (let x = open('file.txt')) {
    print(x);
    var x = 20;
    x = x * 2;
    print(x);
}
print(x);
"""
block_with_result = """
x = 10
with open('file.txt') as _typh_vr_m0_0_x:
    print(_typh_vr_m0_0_x)
    _typh_vr_m0_1_x = 20
    _typh_vr_m0_1_x = _typh_vr_m0_1_x * 2
    print(_typh_vr_m0_1_x)
print(x)
"""


def test_block_with():
    assert_ast_transform(block_with_code, block_with_result)


block_with_immutable_error_code = """
var x = 10;
with (let x = open('file.txt')) {
    x = open('another_file.txt');
}
"""


def test_block_with_immutable_error():
    assert_transform_error(
        block_with_immutable_error_code, ScopeError, "assign to immutable"
    )
