from ..assertion_utils import (
    assert_parse,
    assert_transform,
    assert_typh_code_match_unparse,
)
from src.Typhon.Transform.name_generator import (
    get_unwrap_name,
    get_unwrap_error_name,
)

postfix_op_code = """
let a: int? = None;
"""
postfix_op_result = """
a: (int,) = None
"""
postfix_op_transformed = """
a: int | None = None
"""


def test_postfix_op():
    assert_parse(postfix_op_code, postfix_op_result)
    assert_transform(postfix_op_code, postfix_op_transformed)
    assert_typh_code_match_unparse(postfix_op_code)


postfix_op_unwrap_code = """
def unwrap(x: int?, y: int?) -> int {
    let z = x!
    return z * x!- y!;
}
"""
postfix_op_unwrap_result = """
def unwrap(x: (int,), y: (int,)) -> int:
    z = (x,)
    return z * (x,) - (y,)
"""
postfix_op_unwrap_transformed = f"""
def {get_unwrap_name()}[T](value: T | None) -> T:
    if value is None:
        raise {get_unwrap_error_name()}('Unwrapped None')
    return value

def unwrap(x: int | None, y: int | None) -> int:
    z = {get_unwrap_name()}(x)
    return z * {get_unwrap_name()}(x) - {get_unwrap_name()}(y)
"""


def test_postfix_op_unwrap():
    assert_parse(postfix_op_unwrap_code, postfix_op_unwrap_result)
    assert_transform(postfix_op_unwrap_code, postfix_op_unwrap_transformed)
    assert_typh_code_match_unparse(postfix_op_unwrap_code)


optional_chain_code = """
def func(x: list[int]?) -> int? {
    return x ?.count(42)
}
"""
optional_chain_result = """
def func(x: (list[int],)) -> (int,):
    return x.count(42)
"""
optional_chain_transformed = """
def func(x: list[int] | None) -> int | None:
    return (_typh_vr_f1_0_.count if (_typh_vr_f1_0_ := x) is not None else None)(42)
"""


def test_optional_chain():
    assert_parse(optional_chain_code, optional_chain_result)
    assert_transform(optional_chain_code, optional_chain_transformed)
    assert_typh_code_match_unparse(optional_chain_code)


optional_coalesce_code = """
def func(x: int?) -> int {
    return x ?? 0
}
"""
optional_coalesce_result = """
def func(x: (int,)) -> int:
    return (x, 0)
"""
optional_coalesce_transformed = """
def func(x: int | None) -> int:
    return _typh_vr_f1_0_ if (_typh_vr_f1_0_ := x) is not None else 0
"""


def test_optional_coalesce():
    assert_parse(optional_coalesce_code, optional_coalesce_result)
    assert_transform(optional_coalesce_code, optional_coalesce_transformed)
    assert_typh_code_match_unparse(optional_coalesce_code)


optional_call_code = """
def func(f: ((int) -> int?)?) -> int? {
    return f?(42);
}
"""
optional_call_result = """
def func(f: (__arrow_type,)) -> (int,):
    return f(42)
"""
optional_call_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_1(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_1_a0: int, /) -> int | None:
        ...

def func(f: _typh_ar_f1_1 | None) -> int | None:
    return _typh_vr_f1_0_(42) if (_typh_vr_f1_0_ := f) is not None else None
"""


def test_optional_call():
    assert_parse(optional_call_code, optional_call_result)
    assert_transform(optional_call_code, optional_call_transformed)
    assert_typh_code_match_unparse(optional_call_code)


optional_subscript_code = """
def func(a: list[int]?) -> int? {
    return a?[0];
}
"""
optional_subscript_result = """
def func(a: (list[int],)) -> (int,):
    return a[0]
"""
optional_subscript_transformed = """
def func(a: list[int] | None) -> int | None:
    return _typh_vr_f1_0_[0] if (_typh_vr_f1_0_ := a) is not None else None
"""


def test_optional_subscript():
    assert_parse(optional_subscript_code, optional_subscript_result)
    assert_transform(optional_subscript_code, optional_subscript_transformed)
    assert_typh_code_match_unparse(optional_subscript_code)


optional_nested_code = """
def func(f: ((int?)-> int?)?, a: list[int?]?) -> int {
    return f?(a?[0]) ?? 0;
}
"""

optional_nested_result = """
def func(f: (__arrow_type,), a: (list[int,],)) -> int:
    return (f(a[0]), 0)
"""
optional_nested_transformed = """
from typing import Protocol as _typh_bi_Protocol

class _typh_ar_f1_3(_typh_bi_Protocol):

    def __call__(self, _typh_ar_f1_3_a0: int | None, /) -> int | None:
        ...

def func(f: _typh_ar_f1_3 | None, a: list[int | None] | None) -> int:
    return _typh_vr_f1_0_ if (_typh_vr_f1_0_ := (_typh_vr_f1_1_(_typh_vr_f1_2_[0] if (_typh_vr_f1_2_ := a) is not None else None) if (_typh_vr_f1_1_ := f) is not None else None)) is not None else 0
"""


def test_optional_nested():
    assert_parse(optional_nested_code, optional_nested_result)
    assert_transform(optional_nested_code, optional_nested_transformed)
    assert_typh_code_match_unparse(optional_nested_code)
