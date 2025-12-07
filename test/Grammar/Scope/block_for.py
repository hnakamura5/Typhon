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
for (var (a: int, b: float) in [(1, 1.0), (2, 2.0)]) {
    print(a);
    print(b);
}
"""
for_unpack_typed_result = """
for _typh_vr_m0_1__typh_vr_m0_0_ in [(1, 1.0), (2, 2.0)]:
    _typh_cn_m0_2_a: int
    _typh_cn_m0_3_b: float
    match _typh_vr_m0_1__typh_vr_m0_0_:
        case tuple([_typh_cn_m0_2_a, _typh_cn_m0_3_b]):
            print(_typh_cn_m0_2_a)
            print(_typh_cn_m0_3_b)
        case _:
            raise TypeError
"""


def test_stmt_for_unpack_typed():
    assert_ast_transform(for_unpack_typed_code, for_unpack_typed_result)


code_for_typed_arrow = """
def func(fs: list[int -> str -> float]) -> None {
    for (var f: int -> str -> float in fs) {
        print(f(10)("test"));
    }
}
"""
result_for_typed_arrow = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_0_a0: int, /) -> _typh_ar_f1_1:
        ...

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: str, /) -> float:
        ...

class _typh_ar_f1_2(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_2_a0: int, /) -> _typh_ar_f1_3:
        ...

class _typh_ar_f1_3(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_3_a0: str, /) -> float:
        ...

def func(fs: list[_typh_ar_f1_0]) -> None:
    f: _typh_ar_f1_2
    for f in fs:
        print(f(10)('test'))
"""


def test_stmt_for_typed_arrow():
    assert_ast_transform(code_for_typed_arrow, result_for_typed_arrow)
