from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_transform_error,
    assert_code_match_unparse,
)


placeholder_func_literal_code = """
def apply_func(f: (int, int) -> int, x: int) -> ((int) -> int) {
    return f(x, _)
}
"""
placeholder_func_literal_result = """
def apply_func(f: __arrow_type, x: int) -> __arrow_type:
    return f(x, _)
"""
placeholder_func_literal_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: int, _typh_ar_f1_1_a1: int, /) -> int:
        ...

class _typh_ar_f1_2(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_2_a0: int, /) -> int:
        ...

def apply_func(f: _typh_ar_f1_1, x: int) -> _typh_ar_f1_2:
    return lambda _typh_ag_f1_0_0, /: f(x, _typh_ag_f1_0_0)
"""


def test_exp_placeholder_func_literal():
    parsed = assert_ast_equals(
        placeholder_func_literal_code, placeholder_func_literal_result
    )
    assert_transform_equals(parsed, placeholder_func_literal_transformed)
    assert_code_match_unparse(placeholder_func_literal_code)


placeholder_multiple_code = """
let f = _ * _ + _;
"""
placeholder_multiple_result = """
f = _ * _ + _
"""
placeholder_multiple_transformed = """
f = lambda _typh_ag_m0_0_0, _typh_ag_m0_1_1, _typh_ag_m0_2_2, /: _typh_ag_m0_0_0 * _typh_ag_m0_1_1 + _typh_ag_m0_2_2
"""


def test_exp_placeholder_multiple():
    parsed = assert_ast_equals(placeholder_multiple_code, placeholder_multiple_result)
    assert_transform_equals(parsed, placeholder_multiple_transformed)
    assert_code_match_unparse(placeholder_multiple_code)


placeholder_func_literal_kw_code = """
def apply_func(f: (int, int, int, kw:int) -> int, x: int) -> ((int, int, int) -> int) {
    return f(_, x, _, kw=_)
}
"""
placeholder_func_literal_kw_result = """
def apply_func(f: __arrow_type, x: int) -> __arrow_type:
    return f(_, x, _, kw=_)
"""
placeholder_func_literal_kw_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_3(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_3_a0: int, _typh_ar_f1_3_a1: int, _typh_ar_f1_3_a2: int, /, kw: int) -> int:
        ...

class _typh_ar_f1_4(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_4_a0: int, _typh_ar_f1_4_a1: int, _typh_ar_f1_4_a2: int, /) -> int:
        ...

def apply_func(f: _typh_ar_f1_3, x: int) -> _typh_ar_f1_4:
    return lambda _typh_ag_f1_0_0, _typh_ag_f1_1_1, _typh_ag_f1_2_2, /: f(_typh_ag_f1_0_0, x, _typh_ag_f1_1_1, kw=_typh_ag_f1_2_2)
"""


def test_exp_placeholder_func_literal_kw_kw():
    parsed = assert_ast_equals(
        placeholder_func_literal_kw_code, placeholder_func_literal_kw_result
    )
    assert_transform_equals(parsed, placeholder_func_literal_kw_transformed)
    assert_code_match_unparse(placeholder_func_literal_kw_code)


placeholder_boundary_code = """
def func(x: [int]) -> [int] {
    return x |> map(_ + 1, _)
}
"""
placeholder_nested_result = """
def func(x: [int]) -> [int]:
    return map(_ + 1, _)(x)
"""
placeholder_nested_transformed = """
def func(x: list[int]) -> list[int]:
    return (lambda _typh_ag_f1_0_0, /: map(lambda _typh_ag_f1_1_0, /: _typh_ag_f1_1_0 + 1, _typh_ag_f1_0_0))(x)
"""


def test_exp_placeholder_nested():
    parsed = assert_ast_equals(placeholder_boundary_code, placeholder_nested_result)
    assert_transform_equals(parsed, placeholder_nested_transformed)
    assert_code_match_unparse(placeholder_boundary_code)


placeholder_alone_error_code = """
def func(x: int) -> int {
    return _
}
"""


def placeholder_alone_error_transformed():
    assert_transform_error(placeholder_alone_error_code, SyntaxError)
