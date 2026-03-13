from ..assertion_utils import assert_transform, assert_transform_first_error
from Typhon.Grammar.syntax_errors import ScopeError

block_try_code = """
var x = 10;
try {
    print(x);
    var x = 20;
    x = x + 5;
    print(x);
} except (Exception as x) {
    print(x);
    var x = 5;
    print(x);
    x = x * 2;
}
print(x);
"""

block_try_result = """
from typing import Final as _typh_bi_Final
x = 10
try:
    print(x)
    $x1 = 20
    $x1 = $x1 + 5
    print($x1)
except Exception as $x2:
    $x2: _typh_bi_Final
    print($x2)
    $x3 = 5
    print($x3)
    $x3 = $x3 * 2
print(x)


"""


def test_block_try():
    assert_transform(block_try_code, block_try_result)


block_try_full_code = """
let x = 10;
try {
    print(x);
    let x = 20;
    print(x);
} except (Exception as x) {
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
from typing import Final as _typh_bi_Final
x: _typh_bi_Final = 10
try:
    print(x)
    $x1: _typh_bi_Final = 20
    print($x1)
except Exception as $x2:
    $x2: _typh_bi_Final
    print($x2)
    $x3: _typh_bi_Final = 5
    print($x3)
else:
    print(x)
    $x4: _typh_bi_Final = 15
    print($x4)
finally:
    print(x)
    $x5: _typh_bi_Final = 100
    print($x5)
print(x)
"""


def test_block_try_full():
    assert_transform(block_try_full_code, block_try_full_result)


block_try_except_immutable_error_code = """
let x = 10;
try {
    print(x);
} except (Exception as x) {
    x = TypeError("error");
}
"""


def test_block_try_except_immutable_error():
    assert_transform_first_error(
        block_try_except_immutable_error_code, ScopeError, "assign to immutable"
    )
