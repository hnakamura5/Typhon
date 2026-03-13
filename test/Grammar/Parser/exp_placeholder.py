from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_transform_first_error,
    assert_typh_code_match_unparse,
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

class $func_type1(_typh_bi_Protocol):

    def __call__(self, $arg1: int, $arg2: int, /) -> int:
        ...

class $func_type2(_typh_bi_Protocol):

    def __call__(self, $arg3: int, /) -> int:
        ...

def apply_func(f: $func_type1, x: int) -> $func_type2:
    return lambda $x0, /: f(x, $x0)
"""


def test_exp_placeholder_func_literal():
    parsed = assert_parse(
        placeholder_func_literal_code, placeholder_func_literal_result
    )
    assert_transform_ast(parsed, placeholder_func_literal_transformed)
    assert_typh_code_match_unparse(placeholder_func_literal_code)


placeholder_multiple_code = """
var f = _ * _ + _;
"""
placeholder_multiple_result = """
f = _ * _ + _
"""
placeholder_multiple_transformed = """
f = lambda $x0, $x1, $x2, /: $x0 * $x1 + $x2
"""


def test_exp_placeholder_multiple():
    parsed = assert_parse(placeholder_multiple_code, placeholder_multiple_result)
    assert_transform_ast(parsed, placeholder_multiple_transformed)
    assert_typh_code_match_unparse(placeholder_multiple_code)


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

class $func_type3(_typh_bi_Protocol):

    def __call__(self, $arg1: int, $arg2: int, $arg3: int, /, kw: int) -> int:
        ...

class $func_type4(_typh_bi_Protocol):

    def __call__(self, $arg4: int, $arg5: int, $arg6: int, /) -> int:
        ...

def apply_func(f: $func_type3, x: int) -> $func_type4:
    return lambda $x0, $x1, $x2, /: f($x0, x, $x1, kw=$x2)
"""


def test_exp_placeholder_func_literal_kw_kw():
    parsed = assert_parse(
        placeholder_func_literal_kw_code, placeholder_func_literal_kw_result
    )
    assert_transform_ast(parsed, placeholder_func_literal_kw_transformed)
    assert_typh_code_match_unparse(placeholder_func_literal_kw_code)


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
    return (lambda $x0, /: map(lambda $x1, /: $x1 + 1, $x0))(x)
"""


def test_exp_placeholder_nested():
    parsed = assert_parse(placeholder_boundary_code, placeholder_nested_result)
    assert_transform_ast(parsed, placeholder_nested_transformed)
    assert_typh_code_match_unparse(placeholder_boundary_code)


placeholder_alone_error_code = """
def func(x: int) -> int {
    return _
}
"""


def placeholder_alone_error_transformed():
    assert_transform_first_error(placeholder_alone_error_code, SyntaxError)
