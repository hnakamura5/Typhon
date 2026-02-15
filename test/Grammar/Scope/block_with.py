from ..assertion_utils import assert_transform, assert_transform_first_error
from Typhon.Grammar.syntax_errors import ScopeError

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
from typing import Final as _typh_bi_Final
x: _typh_bi_Final = 10
with open('file.txt') as _typh_cn_m0_0_x:
    _typh_cn_m0_0_x: _typh_bi_Final
    print(_typh_cn_m0_0_x)
    _typh_vr_m0_1_x = 20
    _typh_vr_m0_1_x = _typh_vr_m0_1_x * 2
    print(_typh_vr_m0_1_x)
print(x)
"""


def test_block_with():
    assert_transform(block_with_code, block_with_result)


block_with_immutable_error_code = """
var x = 10;
with (let x = open('file.txt')) {
    x = open('another_file.txt');
}
"""


def test_block_with_immutable_error():
    assert_transform_first_error(
        block_with_immutable_error_code, ScopeError, "assign to immutable"
    )


block_with_top_level_rename_code = """
with (let x = open('file.txt')) {
    def f() {
        print(x);
    }
}
"""
block_with_top_level_rename_result = """
from typing import Final as _typh_bi_Final
with open('file.txt') as _typh_cn_m0_0_x:
    _typh_cn_m0_0_x: _typh_bi_Final

    def _typh_df_f1_0_f():
        print(_typh_cn_m0_0_x)
"""


def test_block_with_top_level_rename():
    assert_transform(
        block_with_top_level_rename_code, block_with_top_level_rename_result
    )


block_with_annotation_code = """
with (let f: TextIO = open('file.txt')) {
    let line = f.readline();
}
"""
block_with_annotation_result = """
from typing import Final as _typh_bi_Final
with open('file.txt') as _typh_cn_m0_0_f:
    _typh_cn_m0_0_f: _typh_bi_Final[TextIO]
    _typh_cn_m0_1_line: _typh_bi_Final = _typh_cn_m0_0_f.readline()
"""


def test_block_with_annotation():
    assert_transform(block_with_annotation_code, block_with_annotation_result)


block_with_multi_annotation_code = """
with (let f1: TextIO = open('file.txt'), f2: TextIO = open('file2.txt')) {
    let line1 = f1.readline();
    let line2 = f2.readline();
}
"""
block_with_multi_annotation_result = """
from typing import Final as _typh_bi_Final
with open('file.txt') as _typh_cn_m0_0_f1, open('file2.txt') as _typh_cn_m0_1_f2:
    _typh_cn_m0_0_f1: _typh_bi_Final[TextIO]
    _typh_cn_m0_1_f2: _typh_bi_Final[TextIO]
    _typh_cn_m0_2_line1: _typh_bi_Final = _typh_cn_m0_0_f1.readline()
    _typh_cn_m0_3_line2: _typh_bi_Final = _typh_cn_m0_1_f2.readline()
"""


def test_block_with_multi_annotation():
    assert_transform(
        block_with_multi_annotation_code, block_with_multi_annotation_result
    )


block_with_star_annotation_code = """
def f() {
    ...
}
with (let (f1: TextIO, f2: TextIO) = f()) {
    let line1 = f1.readline();
    let line2 = f2.readline();
}
"""
block_with_star_annotation_result = """
from typing import Final as _typh_bi_Final

def f():
    ...
with f() as _typh_vr_m0_0_:
    _typh_vr_m0_0_: _typh_bi_Final
    match _typh_vr_m0_0_:
        case tuple([_typh_cn_m0_1_f1, _typh_cn_m0_2_f2]):
            _typh_cn_m0_1_f1: _typh_bi_Final[TextIO]
            _typh_cn_m0_2_f2: _typh_bi_Final[TextIO]
            _typh_cn_m0_3_line1: _typh_bi_Final = _typh_cn_m0_1_f1.readline()
            _typh_cn_m0_4_line2: _typh_bi_Final = _typh_cn_m0_2_f2.readline()
        case _:# type: ignore[all]
            raise TypeError
"""


def test_block_with_star_annotation():
    assert_transform(block_with_star_annotation_code, block_with_star_annotation_result)


inline_with_let_code = """
def f() {
    ...
}
def g() {
    with let (f1, f2) = f()
    f1.readline()
    f2.readline()
}
"""
inline_with_let_result = """
from typing import Final as _typh_bi_Final

def f():
    ...

def g():
    with f() as _typh_vr_f2_0_:
        _typh_vr_f2_0_: _typh_bi_Final
        match _typh_vr_f2_0_:
            case tuple([f1, f2]):
                f1: _typh_bi_Final
                f2: _typh_bi_Final
                f1.readline()
                f2.readline()
            case _:# type: ignore[all]
                raise TypeError
"""


def test_inline_with_let():
    assert_transform(inline_with_let_code, inline_with_let_result)
