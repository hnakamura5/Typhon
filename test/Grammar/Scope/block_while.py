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
    $x1 = x - 1
    print($x1)
    $x1 = $x1 - 2
"""


def test_block_while():
    assert_transform(block_while_code, block_while_result)
