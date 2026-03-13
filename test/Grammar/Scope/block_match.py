from ..assertion_utils import assert_transform, assert_transform_first_error
from Typhon.Grammar.syntax_errors import ScopeError

block_match_code = """
let x = 10;
match (x) {
    case (x, y) if (x > 5) {
        print(x);
        var x = 20;
        x = x + y;
        print(x);
    }
    case (y, *x) if (len(x) > 2) {
        print(x);
        var x = 5;
        print(x);
        x = x * 2;
    }
    case(x) {
        print(x);
        let x = 100;
        print(x);
    }
    case(_) {
        print(x);
        let x = 100;
        print(x);
    }
}
print(x);
"""

block_match_result = """
from typing import Final as _typh_bi_Final
x: _typh_bi_Final = 10
match x:
    case tuple([$x1, $y1]) if $x1 > 5:
        $x1: _typh_bi_Final
        $y1: _typh_bi_Final
        print($x1)
        $x2 = 20
        $x2 = $x2 + $y1
        print($x2)
    case tuple([$y2, *$x3]) if len($x3) > 2:
        $y2: _typh_bi_Final
        $x3: _typh_bi_Final
        print($x3)
        $x4 = 5
        print($x4)
        $x4 = $x4 * 2
    case $x5:
        $x5: _typh_bi_Final
        print($x5)
        $x6: _typh_bi_Final = 100
        print($x6)
    case _:
        print(x)
        $x7: _typh_bi_Final = 100
        print($x7)
print(x)
"""


def test_block_match():
    assert_transform(block_match_code, block_match_result)
