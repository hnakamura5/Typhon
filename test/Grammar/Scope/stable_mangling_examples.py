from ..assertion_utils import assert_transform


block_if_stable_mangling_code = """
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

block_if_stable_mangling_result = """
x = 10
if x > 5:
    print(x)
    _typh_v_7dfcujdv_x = 20
    print(_typh_v_7dfcujdv_x + 1)
    _typh_v_7dfcujdv_x = 30
else:
    _typh_v_5xhqwzpt_x = 5
    print(_typh_v_5xhqwzpt_x)
    _typh_v_5xhqwzpt_x = 40
"""


def test_block_if_uses_decl_anchored_mangling() -> None:
    assert_transform(block_if_stable_mangling_code, block_if_stable_mangling_result)


optional_temp_stable_mangling_code = """
var f: ((int) -> int)? = None;
var x = f?(1);
"""

optional_temp_stable_mangling_result = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_w2oip4s3(_typh_bi_Protocol):

    def __call__(self, _typh_a_77ez2osh: int, /) -> int:
        ...
f: _typh_ar_w2oip4s3 | None = None
x = _typh_v_fimh5dnn(1) if (_typh_v_fimh5dnn := f) is not None else None
"""


def test_optional_temp_uses_role_suffix() -> None:
    assert_transform(
        optional_temp_stable_mangling_code,
        optional_temp_stable_mangling_result,
    )


func_literal_stable_mangling_code = """
var f = (x: int) => x + 1;
"""

func_literal_stable_mangling_result = """
def _typh_lf_5tgziudd(x: int):
    return x + 1
f = _typh_lf_5tgziudd
"""


def test_function_literal_uses_origin_based_name() -> None:
    assert_transform(
        func_literal_stable_mangling_code,
        func_literal_stable_mangling_result,
    )


if_let_flag_stable_mangling_code = """
var value = 1;
if (let x = value) {
    print(x)
} else {
    print(0)
}
"""

if_let_flag_stable_mangling_result = """
from typing import Final as _typh_bi_Final
value = 1
_typh_v_fimh5dnn = True
match value:
    case _typh_c_wyy7weq4_x if _typh_c_wyy7weq4_x is not None:
        _typh_c_wyy7weq4_x: _typh_bi_Final
        _typh_v_fimh5dnn = False
        print(_typh_c_wyy7weq4_x)
    case _:
        pass
if _typh_v_fimh5dnn:
    print(0)
"""


def test_if_let_flag_uses_role_suffix() -> None:
    assert_transform(
        if_let_flag_stable_mangling_code,
        if_let_flag_stable_mangling_result,
    )
