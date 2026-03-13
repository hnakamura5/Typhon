from ..assertion_utils import assert_transform

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
from typing import Final as _typh_bi_Final
x = range(5)
for $x1 in x:
    $x1: _typh_bi_Final
    print($x1)
    $x2 = $x1 + 1
    print($x2)
    $x2 = $x2 + 2
"""


def test_block_for():
    assert_transform(block_for_code, block_for_result)


for_unpack_typed_code = """
for (let (a: int, b: float) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
for_unpack_typed_result = """
from typing import Final as _typh_bi_Final
for $anonymous1 in [(1, 1.0), (2, 2.0)]:
    $anonymous1: _typh_bi_Final
    match $anonymous1:
        case tuple([$a, $b]):
            $a: _typh_bi_Final[int]
            $b: _typh_bi_Final[float]
            print($a)
            print($b)
        case _:# type: ignore[all]
            raise TypeError
"""


def test_stmt_for_unpack_typed():
    assert_transform(for_unpack_typed_code, for_unpack_typed_result)


code_for_typed_arrow = """
def func(fs: list[int -> str -> float]) -> None {
    for (var f: int -> str -> float in fs) {
        print(f(10)("test"));
    }
}
"""
result_for_typed_arrow = """
from typing import Protocol as _typh_bi_Protocol

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $a0_1: int, /) -> $func_type2:
        ...

class $func_type2(_typh_bi_Protocol):

    def __call__(self, $a0_2: str, /) -> float:
        ...

class $func_type3(_typh_bi_Protocol):

    def __call__(self, $a0_3: int, /) -> $func_type4:
        ...

class $func_type4(_typh_bi_Protocol):

    def __call__(self, $a0_4: str, /) -> float:
        ...

def func(fs: list[$func_type1]) -> None:
    for f in fs:
        f: $func_type3
        print(f(10)('test'))
"""


def test_stmt_for_typed_arrow():
    assert_transform(code_for_typed_arrow, result_for_typed_arrow)
