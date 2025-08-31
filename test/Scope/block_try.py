from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Grammar.syntax_errors import ScopeError

block_try_code = """
let x = 10;
try {
    print(x);
    let x = 20;
    x = x + 5;
    print(x);
} except (x: Exception) {
    print(x);
    let x = 5;
    print(x);
    x = x * 2;
}
print(x);
"""
block_try_result = """
x = 10
try:
    print(x)
    _typh_vr_m0_0_x = 20
    _typh_vr_m0_0_x = _typh_vr_m0_0_x + 5
    print(_typh_vr_m0_0_x)
except Exception as _typh_vr_m0_1_x:
    print(_typh_vr_m0_1_x)
    _typh_vr_m0_2_x = 5
    print(_typh_vr_m0_2_x)
    _typh_vr_m0_2_x = _typh_vr_m0_2_x * 2
print(x)
"""


def test_block_try():
    assert_ast_transform(block_try_code, block_try_result)


block_try_full_code = """
let x = 10;
try {
    print(x);
    let x = 20;
    print(x);
} except (x: Exception) {
    print(x);
    let x = 5;
    print(x);
} else {
    print(x);
    let x = 15;
    print(x);
} finally {
    print(x);
    let x = 100;
    print(x);
}
print(x);
"""
block_try_full_result = """
x = 10
try:
    print(x)
    _typh_vr_m0_0_x = 20
    print(_typh_vr_m0_0_x)
except Exception as _typh_vr_m0_1_x:
    print(_typh_vr_m0_1_x)
    _typh_vr_m0_2_x = 5
    print(_typh_vr_m0_2_x)
else:
    print(x)
    _typh_vr_m0_3_x = 15
    print(_typh_vr_m0_3_x)
finally:
    print(x)
    _typh_vr_m0_4_x = 100
    print(_typh_vr_m0_4_x)
print(x)
"""


def test_block_try_full():
    assert_ast_transform(block_try_full_code, block_try_full_result)


block_try_except_immutable_error_code = """
let x = 10;
try {
    print(x);
} except (x: Exception) {
    x = TypeError("error");
}
"""


def test_block_try_except_immutable_error():
    assert_transform_error(
        block_try_except_immutable_error_code, ScopeError, "assign to immutable"
    )
