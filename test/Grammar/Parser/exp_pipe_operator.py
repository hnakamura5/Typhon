from ..assertion_utils import (
    assert_parse,
    assert_transform,
    assert_typh_code_match_unparse,
)

# Note second pipe is inside the first function literal.
pipe_operator_code = """
def func(x: int) -> int {
    return x |> (x) => x * 2
                         |> (y) => x + y
}
"""
pipe_operator_result = """
def func(x: int) -> int:
    return (lambda x: (lambda y: x + y)(x * 2))(x)
"""
pipe_operator_transform = """
def func(x: int) -> int:
    return (lambda x: (lambda y: x + y)(x * 2))(x)
"""


def test_pipe_operator():
    assert_parse(pipe_operator_code, pipe_operator_result)
    assert_transform(pipe_operator_code, pipe_operator_transform)
    assert_typh_code_match_unparse(pipe_operator_code)


pipe_operator_pipeline_code = """
def func(x: int) -> int {
    return x |> ((x) => x * 2)
             |> ((x) => x + 1)
}
"""
pipe_operator_pipeline_result = """
def func(x: int) -> int:
    return (lambda x: x + 1)((lambda x: x * 2)(x))
"""
pipe_operator_pipeline_transformed = """
def func(x: int) -> int:
    return (lambda x: x + 1)((lambda x: x * 2)(x))
"""


def test_pipe_operator_pipeline():
    assert_parse(pipe_operator_pipeline_code, pipe_operator_pipeline_result)
    assert_transform(pipe_operator_pipeline_code, pipe_operator_pipeline_transformed)
    assert_typh_code_match_unparse(pipe_operator_pipeline_code)


optional_pipe_operator_code = """
def func(x: int?) -> int? {
    return x ?|> (x) => x * 2
             ?|> (x) => x + 1
}
"""
optional_pipe_operator_result = """
def func(x: (int,)) -> (int,):
    return (lambda x: (lambda x: x + 1)(x * 2))(x)
"""


optional_pipe_operator_transformed = """
def func(x: int | None) -> int | None:
    return (lambda x: (lambda x: x + 1)(_typh_vr_f1_1_) if (_typh_vr_f1_1_ := (x * 2)) is not None else None)(_typh_vr_f1_0_) if (_typh_vr_f1_0_ := x) is not None else None
"""


def test_optional_pipe_operator():
    assert_parse(optional_pipe_operator_code, optional_pipe_operator_result)
    assert_transform(optional_pipe_operator_code, optional_pipe_operator_transformed)
    assert_typh_code_match_unparse(optional_pipe_operator_code)


pipe_placeholder_code = """
def func(x: [int]) -> [int] {
    return x |> map((y) => y * 2, _) |> filter((y) => y > 0, _) |> list
}
"""
pipe_placeholder_result = """
def func(x: [int]) -> [int]:
    return list(filter(lambda y: y > 0, _)(map(lambda y: y * 2, _)(x)))
"""
pipe_placeholder_transformed = """
def func(x: list[int]) -> list[int]:
    return list((lambda _typh_ag_f1_0_0, /: filter(lambda y: y > 0, _typh_ag_f1_0_0))((lambda _typh_ag_f1_1_0, /: map(lambda y: y * 2, _typh_ag_f1_1_0))(x)))
"""


def test_pipe_placeholder():
    assert_parse(pipe_placeholder_code, pipe_placeholder_result)
    assert_transform(pipe_placeholder_code, pipe_placeholder_transformed)
    assert_typh_code_match_unparse(pipe_placeholder_code)


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
        pipe_left_associative_symbols_code, pipe_left_associative_symbols_result
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
