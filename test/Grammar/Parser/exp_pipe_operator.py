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
