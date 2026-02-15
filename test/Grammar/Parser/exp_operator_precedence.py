from ..assertion_utils import (
    assert_parse,
    assert_transform,
    assert_typh_code_match_unparse,
)


logical_and_or_precedence_code = """
def func(x: bool, y: bool, z: bool) -> bool {
    return x || y && z
}
"""
logical_and_or_precedence_result = """
def func(x: bool, y: bool, z: bool) -> bool:
    return x or (y and z)
"""
logical_and_or_precedence_transformed = """
def func(x: bool, y: bool, z: bool) -> bool:
    return x or (y and z)
"""


def test_logical_and_or_precedence():
    assert_parse(logical_and_or_precedence_code, logical_and_or_precedence_result)
    assert_transform(
        logical_and_or_precedence_code,
        logical_and_or_precedence_transformed,
    )
    assert_typh_code_match_unparse(logical_and_or_precedence_code)


pipe_left_associative_symbols_code = """
def func(x: int) -> int {
    let f = (v) => v + 1
    let g = (v) => v * 2
    let h = (v) => v - 3
    return x |> f |> g |> h
}
"""
pipe_left_associative_symbols_result = """
def func(x: int) -> int:
    f = lambda v: v + 1
    g = lambda v: v * 2
    h = lambda v: v - 3
    return h(g(f(x)))
"""
pipe_left_associative_symbols_transformed = """
from typing import Final as _typh_bi_Final

def func(x: int) -> int:
    f: _typh_bi_Final = lambda v: v + 1
    g: _typh_bi_Final = lambda v: v * 2
    h: _typh_bi_Final = lambda v: v - 3
    return h(g(f(x)))
"""


def test_pipe_left_associative_symbols():
    assert_parse(
        pipe_left_associative_symbols_code,
        pipe_left_associative_symbols_result,
    )
    assert_transform(
        pipe_left_associative_symbols_code,
        pipe_left_associative_symbols_transformed,
    )
    assert_typh_code_match_unparse(pipe_left_associative_symbols_code)


pipe_precedence_vs_coalescing_code = """
def func(x: int?, y: int?) -> int? {
    let f = (z) => z
    return x ?? y |> f
}
"""
pipe_precedence_vs_coalescing_result = """
def func(x: (int,), y: (int,)) -> (int,):
    f = lambda z: z
    return f((x, y))
"""
pipe_precedence_vs_coalescing_transformed = """
from typing import Final as _typh_bi_Final

def func(x: int | None, y: int | None) -> int | None:
    f: _typh_bi_Final = lambda z: z
    return f(_typh_vr_f1_0_ if (_typh_vr_f1_0_ := x) is not None else y)
"""


def test_pipe_precedence_vs_coalescing():
    assert_parse(
        pipe_precedence_vs_coalescing_code,
        pipe_precedence_vs_coalescing_result,
    )
    assert_transform(
        pipe_precedence_vs_coalescing_code,
        pipe_precedence_vs_coalescing_transformed,
    )
    assert_typh_code_match_unparse(pipe_precedence_vs_coalescing_code)


pipe_precedence_vs_or_code = """
def func(x: bool, y: bool) -> bool {
    let f = (z) => z
    return x || y |> f
}
"""
pipe_precedence_vs_or_result = """
def func(x: bool, y: bool) -> bool:
    f = lambda z: z
    return f(x or y)
"""
pipe_precedence_vs_or_transformed = """
from typing import Final as _typh_bi_Final

def func(x: bool, y: bool) -> bool:
    f: _typh_bi_Final = lambda z: z
    return f(x or y)
"""


def test_pipe_precedence_vs_or():
    assert_parse(pipe_precedence_vs_or_code, pipe_precedence_vs_or_result)
    assert_transform(pipe_precedence_vs_or_code, pipe_precedence_vs_or_transformed)
    assert_typh_code_match_unparse(pipe_precedence_vs_or_code)


pipe_precedence_vs_sum_code = """
def func(x: int) -> int {
    let f = (z) => z
    return x + 1 |> f
}
"""
pipe_precedence_vs_sum_result = """
def func(x: int) -> int:
    f = lambda z: z
    return f(x + 1)
"""
pipe_precedence_vs_sum_transformed = """
from typing import Final as _typh_bi_Final

def func(x: int) -> int:
    f: _typh_bi_Final = lambda z: z
    return f(x + 1)
"""


def test_pipe_precedence_vs_sum():
    assert_parse(pipe_precedence_vs_sum_code, pipe_precedence_vs_sum_result)
    assert_transform(pipe_precedence_vs_sum_code, pipe_precedence_vs_sum_transformed)
    assert_typh_code_match_unparse(pipe_precedence_vs_sum_code)
