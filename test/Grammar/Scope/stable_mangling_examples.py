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
    $x1 = 20
    print($x1 + 1)
    $x1 = 30
else:
    $x2 = 5
    print($x2)
    $x2 = 40
"""


def test_block_if_uses_decl_anchored_mangling() -> None:
    assert_transform(block_if_stable_mangling_code, block_if_stable_mangling_result)


optional_temp_stable_mangling_code = """
var f: ((int) -> int)? = None;
var x = f?(1);
"""

optional_temp_stable_mangling_result = """
from typing import Protocol as _typh_bi_Protocol

class $f_type(_typh_bi_Protocol):

    def __call__(self, $arg: int, /) -> int:
        ...
f: $f_type | None = None
x = $f_temp(1) if ($f_temp := f) is not None else None
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
def $f_impl(x: int):
    return x + 1
f = $f_impl
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
$flag = True
match value:
    case $x if $x is not None:
        $x: _typh_bi_Final
        $flag = False
        print($x)
    case _:
        pass
if $flag:
    print(0)
"""


def test_if_let_flag_uses_role_suffix() -> None:
    assert_transform(
        if_let_flag_stable_mangling_code,
        if_let_flag_stable_mangling_result,
    )
