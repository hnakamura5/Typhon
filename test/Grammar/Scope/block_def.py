from ..assertion_utils import assert_transform

block_def_code = """
let x = 10;
def f(x: int) -> int {
    let x:int = x + 1;
    return x;
}
"""
block_def_result = """
x = 10

def f(x: int) -> int:
    _typh_cn_f1_0_x: int = x + 1
    return _typh_cn_f1_0_x
"""


def test_block_def():
    assert_transform(block_def_code, block_def_result)


block_def_nested_code = """
let x = 10;
def f(x: int, y: int) -> int {
    let x = x + 1;
    def g(x: int) -> int {
        let x = x + 2;
        let y = x * y;
        return y;
    }
    return g(x) + y;
}
"""
block_def_nested_result = """
x = 10

def f(x: int, y: int) -> int:
    _typh_cn_f1_0_x = x + 1

    def g(x: int) -> int:
        _typh_cn_f2_0_x = x + 2
        _typh_cn_f2_1_y = _typh_cn_f2_0_x * y
        return _typh_cn_f2_1_y
    return g(_typh_cn_f1_0_x) + y
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
def f[T](x: T) -> T:
    y: T = x
    return y
"""


def test_block_def_type_param():
    assert_transform(block_def_type_param_code, block_def_type_param_result)
