from ..assertion_utils import assert_transform

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
    $x1 = 20
    print($x1 + 1)
    $x1 = 30
else:
    $x2 = 5
    print($x2)
    $x2 = 40
"""


def test_block_if():
    assert_transform(block_if_code, block_if_result)


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
    $x1 = 20
    if $x1 <= 20:
        print($x1)
        $x1 = 15
        $x2 = 5
        print($x2)
"""


def test_block_if_nested():
    assert_transform(block_if_nested_code, block_if_nested_result)


block_if_top_level_rename_code = """
if (True) {
    var x = 10;
}
"""
block_if_top_level_rename_result = """
if True:
    $x = 10
"""


def test_block_if_top_level_rename():
    assert_transform(block_if_top_level_rename_code, block_if_top_level_rename_result)
