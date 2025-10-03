from ..assertion_utils import (
    assert_ast_equals,
    assert_ast_transform,
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
    return __function_literal(x)
"""
pipe_operator_transform = """
def func(x: int) -> int:

    def _typh_fn_f1_0(x):

        def _typh_fn_f2_0(y):
            return x + y
        return _typh_fn_f2_0(x * 2)
    return _typh_fn_f1_0(x)
"""


def test_pipe_operator():
    assert_ast_equals(pipe_operator_code, pipe_operator_result)
    assert_ast_transform(pipe_operator_code, pipe_operator_transform)


pipe_operator_pipeline_code = """
def func(x: int) -> int {
    return x |> ((x) => x * 2)
             |> ((x) => x + 1)
}
"""
pipe_operator_pipeline_result = """
def func(x: int) -> int:
    return __function_literal(__function_literal(x))
"""
pipe_operator_pipeline_transformed = """
def func(x: int) -> int:

    def _typh_fn_f1_0(x):
        return x + 1

    def _typh_fn_f1_1(x):
        return x * 2
    return _typh_fn_f1_0(_typh_fn_f1_1(x))
"""


def test_pipe_operator_pipeline():
    assert_ast_equals(pipe_operator_pipeline_code, pipe_operator_pipeline_result)
    assert_ast_transform(
        pipe_operator_pipeline_code, pipe_operator_pipeline_transformed
    )


optional_pipe_operator_code = """
def func(x: int?) -> int? {
    return x ?|> (x) => x * 2
             ?|> (x) => x + 1
}
"""
optional_pipe_operator_result = """
def func(x: (int,)) -> (int,):
    return __function_literal(x)
"""


optional_pipe_operator_transformed = """
def func(x: int | None) -> int | None:

    def _typh_fn_f1_0(x):

        def _typh_fn_f2_0(x):
            return x + 1
        return _typh_fn_f2_0(_typh_vr_f2_0_) if (_typh_vr_f2_0_ := (x * 2)) is not None else None
    return _typh_fn_f1_0(_typh_vr_f1_0_) if (_typh_vr_f1_0_ := x) is not None else None
"""


def test_optional_pipe_operator():
    assert_ast_equals(optional_pipe_operator_code, optional_pipe_operator_result)
    assert_ast_transform(
        optional_pipe_operator_code, optional_pipe_operator_transformed
    )


pipe_placeholder_code = """
def func(x: [int]) -> [int] {
    return x |> map((y) => y * 2, ...) |> filter((y) => y > 0, ...) |> list
}
"""
pipe_placeholder_result = """
def func(x: [int]) -> [int]:
    return list(filter(__function_literal, ...)(map(__function_literal, ...)(x)))
"""
pipe_placeholder_transformed = """
def func(x: list[int]) -> list[int]:

    def _typh_fn_f1_0(y):
        return y > 0

    def _typh_fn_f1_1(y):
        return y * 2

    def _typh_fn_f1_3(_typh_ag_f1_2_1):
        return filter(_typh_fn_f1_0, _typh_ag_f1_2_1)

    def _typh_fn_f1_5(_typh_ag_f1_4_1):
        return map(_typh_fn_f1_1, _typh_ag_f1_4_1)
    return list(_typh_fn_f1_3(_typh_fn_f1_5(x)))
"""


def test_pipe_placeholder():
    assert_ast_equals(pipe_placeholder_code, pipe_placeholder_result)
    assert_ast_transform(pipe_placeholder_code, pipe_placeholder_transformed)
