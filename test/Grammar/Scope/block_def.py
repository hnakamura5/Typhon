from ..assertion_utils import assert_transform

block_def_code = """
var x = 10;
def f(x: int) -> int {
    var x:int = x + 1;
    return x;
}
"""
block_def_result = """
x = 10

def f(x: int) -> int:
    $x1: int = x + 1
    return $x1
"""


def test_block_def():
    assert_transform(block_def_code, block_def_result)


block_def_nested_code = """
var x = 10;
def f(x: int, y: int) -> int {
    var x = x + 1;
    def g(x: int) -> int {
        var x = x + 2;
        var y = x * y;
        return y;
    }
    return g(x) + y;
}
"""
block_def_nested_result = """
x = 10

def f(x: int, y: int) -> int:
    $x1 = x + 1

    def g(x: int) -> int:
        $x2 = x + 2
        $y1 = $x2 * y
        return $y1
    return g($x1) + y
"""


def test_block_def_nested():
    assert_transform(block_def_nested_code, block_def_nested_result)


block_def_type_param_code = """
def f[T](x: T) -> T {
    let y: T = x;
    return y;
}
"""
block_def_type_param_result = """
from typing import Final as _typh_bi_Final

def f[T](x: T) -> T:
    y: _typh_bi_Final[T] = x
    return y
"""


def test_block_def_type_param():
    assert_transform(block_def_type_param_code, block_def_type_param_result)
