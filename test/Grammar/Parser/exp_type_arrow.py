from Typhon.Driver.debugging import set_debug_verbose
from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

set_debug_verbose(True)

type_arrow_annot_code = """
var x: (int) -> int;
"""
type_arrow_annot_result = """
x: __arrow_type
"""
type_arrow_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int, /) -> int:
        ...
x: _typh_ar_m0_0
"""


def test_type_arrow_annot():
    parsed = assert_parse(type_arrow_annot_code, type_arrow_annot_result)
    assert_transform_ast(parsed, type_arrow_annot_transformed)
    assert_typh_code_match_unparse(type_arrow_annot_code)


type_arrow_param_annot_code = """
var a: (x: int, y: str) -> int;
"""
type_arrow_param_annot_result = """
a: __arrow_type
"""
type_arrow_param_annot_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, x: int, y: str) -> int:
        ...
a: _typh_ar_m0_0
"""


def test_type_arrow_param_annot():
    parsed = assert_parse(type_arrow_param_annot_code, type_arrow_param_annot_result)
    assert_transform_ast(parsed, type_arrow_param_annot_transformed)
    assert_typh_code_match_unparse(type_arrow_param_annot_code)


type_arrow_def_param_code = """
def h(x: int, f: (int) -> int) -> int {
    return f(x);
}
"""
type_arrow_def_param_result = """
def h(x: int, f: __arrow_type) -> int:
    return f(x)
"""
type_arrow_def_param_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_0_a0: int, /) -> int:
        ...

def h(x: int, f: _typh_ar_f1_0) -> int:
    return f(x)
"""


def test_type_arrow_def_param():
    parsed = assert_parse(type_arrow_def_param_code, type_arrow_def_param_result)
    assert_transform_ast(parsed, type_arrow_def_param_transformed)


type_arrow_func_literal_code = """
var f: (x: int) -> int = (x:int) -> int => {
    return x + 1;
};
"""
type_arrow_func_literal_result = """
f: __arrow_type = __function_literal
"""
type_arrow_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_1(_typh_bi_Protocol):

    def __call__(self, x: int) -> int:
        ...

def _typh_fn_m0_0(x: int) -> int:
    return x + 1
f: _typh_ar_m0_1 = _typh_fn_m0_0
"""


def test_type_arrow_func_literal():
    parsed = assert_parse(type_arrow_func_literal_code, type_arrow_func_literal_result)
    assert_transform_ast(parsed, type_arrow_func_literal_transformed)
    assert_typh_code_match_unparse(type_arrow_func_literal_code)


type_arrow_star_etc_code = """
var f: (float, x: int, *args: str, **kwds: int) -> int;
"""
type_arrow_star_etc_result = """
f: __arrow_type
"""
type_arrow_star_etc_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: float, /, x: int, *args: str, **kwds: int) -> int:
        ...
f: _typh_ar_m0_0
"""


def test_type_arrow_star_etc():
    parsed = assert_parse(type_arrow_star_etc_code, type_arrow_star_etc_result)
    assert_transform_ast(parsed, type_arrow_star_etc_transformed)
    assert_typh_code_match_unparse(type_arrow_star_etc_code)


type_arrow_single_no_paren_code = """
var f: int -> int;
"""
type_arrow_single_no_paren_result = """
f: __arrow_type
"""
type_arrow_single_no_paren_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int, /) -> int:
        ...
f: _typh_ar_m0_0
"""


def test_type_arrow_single_no_paren():
    parsed = assert_parse(
        type_arrow_single_no_paren_code, type_arrow_single_no_paren_result
    )
    assert_transform_ast(parsed, type_arrow_single_no_paren_transformed)
    assert_typh_code_match_unparse(type_arrow_single_no_paren_code)


type_arrow_in_subscript_code = """
var x: list[int -> str];
"""
type_arrow_in_subscript_result = """
x: list[__arrow_type]
"""
type_arrow_in_subscript_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int, /) -> str:
        ...
x: list[_typh_ar_m0_0]
"""


def test_type_arrow_in_subscript():
    parsed = assert_parse(type_arrow_in_subscript_code, type_arrow_in_subscript_result)
    assert_transform_ast(parsed, type_arrow_in_subscript_transformed)
    assert_typh_code_match_unparse(type_arrow_in_subscript_code)


type_arrow_to_subscript_code = """
var x: list[int -> list[str -> float]];
"""
type_arrow_to_subscript_result = """
x: list[__arrow_type]
"""
type_arrow_to_subscript_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int, /) -> list[_typh_ar_m0_1]:
        ...

class _typh_ar_m0_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_1_a0: str, /) -> float:
        ...
x: list[_typh_ar_m0_0]
"""


def test_type_arrow_to_subscript():
    parsed = assert_parse(type_arrow_to_subscript_code, type_arrow_in_subscript_result)
    assert_transform_ast(parsed, type_arrow_to_subscript_transformed)
    assert_typh_code_match_unparse(type_arrow_to_subscript_code)


type_arrow_single_no_paren_chain_code = """
var f: int? -> [int] -> list[str -> float] -> (int -> int) -> (int, float) -> int?;
"""
type_arrow_single_no_paren_chain_result = """
f: __arrow_type
"""
type_arrow_single_no_paren_chain_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_m0_0(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_0_a0: int | None, /) -> _typh_ar_m0_1:
        ...

class _typh_ar_m0_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_1_a0: list[int], /) -> _typh_ar_m0_2:
        ...

class _typh_ar_m0_2(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_2_a0: list[_typh_ar_m0_3], /) -> _typh_ar_m0_4:
        ...

class _typh_ar_m0_3(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_3_a0: str, /) -> float:
        ...

class _typh_ar_m0_4(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_4_a0: _typh_ar_m0_5, /) -> _typh_ar_m0_6:
        ...

class _typh_ar_m0_5(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_5_a0: int, /) -> int:
        ...

class _typh_ar_m0_6(_typh_bi_Protocol):

    def __call__(self, _typh_ar_m0_6_a0: int, _typh_ar_m0_6_a1: float, /) -> int | None:
        ...
f: _typh_ar_m0_0
"""


def test_type_arrow_single_no_paren_chain():
    parsed = assert_parse(
        type_arrow_single_no_paren_chain_code, type_arrow_single_no_paren_chain_result
    )
    assert_transform_ast(parsed, type_arrow_single_no_paren_chain_transformed)
    assert_typh_code_match_unparse(type_arrow_single_no_paren_chain_code)
