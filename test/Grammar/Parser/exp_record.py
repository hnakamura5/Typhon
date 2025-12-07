from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
    assert_ast_error,
    assert_typh_code_match_unparse,
)
from ....src.Typhon.Driver.debugging import set_debug_mode


record_literal_code = """
{|x = 1, y = '2'|}
"""
record_literal_result = """
__record_literal
"""
record_literal_transformed = """
from typing import Final as _typh_bi_Final
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class _typh_cl_m0_2_[_typh_tv_m0_0_x, _typh_tv_m0_1_y]:
    x: _typh_bi_Final[_typh_tv_m0_0_x]
    y: _typh_bi_Final[_typh_tv_m0_1_y]

    def __repr__(self):
        return f'{{|x={self.x!r}, y={self.y!r}|}}'
_typh_cl_m0_2_(x=1, y='2')
"""


def test_record_literal():
    parsed = assert_ast_equals(record_literal_code, record_literal_result)
    assert_transform_equals(parsed, record_literal_transformed)
    assert_typh_code_match_unparse(record_literal_code)


record_literal_positional_error_code = """
def f(x: int) {
    return {|x|}
}
"""


def test_record_literal_positional_error():
    assert_ast_error(record_literal_positional_error_code, SyntaxError)


record_literal_annotation_code = """
{|x = 1, y: str = '2', z = 3|}
"""
record_literal_annotation_result = """
__record_literal
"""
record_literal_annotation_transformed = """
from typing import Final as _typh_bi_Final
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class _typh_cl_m0_2_[_typh_tv_m0_0_x, _typh_tv_m0_1_z]:
    x: _typh_bi_Final[_typh_tv_m0_0_x]
    y: _typh_bi_Final[str]
    z: _typh_bi_Final[_typh_tv_m0_1_z]

    def __repr__(self):
        return f'{{|x={self.x!r}, y={self.y!r}, z={self.z!r}|}}'
_typh_cl_m0_2_(x=1, y='2', z=3)
"""


def test_record_literal_annotation():
    parsed = assert_ast_equals(
        record_literal_annotation_code, record_literal_annotation_result
    )
    assert_transform_equals(parsed, record_literal_annotation_transformed)
    assert_typh_code_match_unparse(record_literal_annotation_code)


record_type_code = """
def func(r: {|x: int, y: str|}) -> None {
    print(r.x, r.y)
}
"""
record_type_result = """
def func(r: __record_type) -> None:
    print(r.x, r.y)
"""
record_type_transformed = """
from typing import Final as _typh_bi_Final
from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_runtime_checkable
@_typh_bi_dataclass(frozen=True, repr=True, unsafe_hash=True, kw_only=True)
class _typh_cl_f1_2_[_typh_tv_f1_0_x, _typh_tv_f1_1_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_0_x]
    y: _typh_bi_Final[_typh_tv_f1_1_y]

def func(r: _typh_cl_f1_2_[int, str]) -> None:
    print(r.x, r.y)
"""


def test_record_type():
    parsed = assert_ast_equals(record_type_code, record_type_result)
    assert_transform_equals(parsed, record_type_transformed)
    assert_typh_code_match_unparse(record_type_code)


record_type_positional_error_code = """
def func(r: {|int, str|}) -> None {
    print(r.x, r.y)
}
"""


def test_record_type_positional_error():
    assert_ast_error(record_type_positional_error_code, SyntaxError)


attribute_pattern_code = """
def f(r) {
    match (r) {
        case ({.x = a, .y = b}) {
            print(a, b)
        }
    }
}
"""
attribute_pattern_result = """
def f(r):
    match r:
        case __attribute_pattern(x=a, y=b):
            print(a, b)
"""
attribute_pattern_transformed = """
from typing import Final as _typh_bi_Final
from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol

@_typh_bi_runtime_checkable
class _typh_cl_f1_2_[_typh_tv_f1_0_x, _typh_tv_f1_1_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_0_x]
    y: _typh_bi_Final[_typh_tv_f1_1_y]

def f(r):
    match r:
        case _typh_cl_f1_2_(x=a, y=b):
            print(a, b)
"""


def test_attribute_pattern():
    parsed = assert_ast_equals(attribute_pattern_code, attribute_pattern_result)
    assert_transform_equals(parsed, attribute_pattern_transformed)
    assert_typh_code_match_unparse(attribute_pattern_code)


attribute_pattern_if_let_code = """
def f(r: {|x: int, y: (int, str)|}) -> None {
    if (let {.x = a, .y = (0, c)} = r) {
        print(a, c)
    } elif (let {.x = a} = r) {
        print(a)
    }
}
f({|x=1, y=(2, 'example')|})
"""
attribute_pattern_if_let_result = """
def f(r: __record_type) -> None:
    if True:
        match r:
            case __attribute_pattern(x=a, y=[0, c]):
                print(a, c)
            case _:
                pass
    elif True:
        match r:
            case __attribute_pattern(x=a):
                print(a)
            case _:
                pass
f(__record_literal)
"""
attribute_pattern_if_let_transformed = """
from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol
from typing import Final as _typh_bi_Final
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_runtime_checkable
class _typh_cl_f1_7_[_typh_tv_f1_6_x](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_6_x]

@_typh_bi_runtime_checkable
class _typh_cl_f1_5_[_typh_tv_f1_3_x, _typh_tv_f1_4_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_3_x]
    y: _typh_bi_Final[_typh_tv_f1_4_y]

@_typh_bi_runtime_checkable
@_typh_bi_dataclass(frozen=True, repr=True, unsafe_hash=True, kw_only=True)
class _typh_cl_f1_2_[_typh_tv_f1_0_x, _typh_tv_f1_1_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_0_x]
    y: _typh_bi_Final[_typh_tv_f1_1_y]

@_typh_bi_dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class _typh_cl_m0_2_[_typh_tv_m0_0_x, _typh_tv_m0_1_y]:
    x: _typh_bi_Final[_typh_tv_m0_0_x]
    y: _typh_bi_Final[_typh_tv_m0_1_y]

    def __repr__(self):
        return f'{{|x={self.x!r}, y={self.y!r}|}}'

def f(r: _typh_cl_f1_2_[int, tuple[int, str]]) -> None:
    _typh_vr_f1_9_ = True
    match r:
        case _typh_cl_f1_5_(x=a, y=tuple([0, c])):
            _typh_vr_f1_9_ = False
            print(a, c)
        case _:
            pass
    if _typh_vr_f1_9_:
        _typh_vr_f1_8_ = True
        match r:
            case _typh_cl_f1_7_(x=a):
                _typh_vr_f1_8_ = False
                print(a)
            case _:
                pass
f(_typh_cl_m0_2_(x=1, y=(2, 'example')))
"""


def test_attribute_pattern_if_let():
    parsed = assert_ast_equals(
        attribute_pattern_if_let_code, attribute_pattern_if_let_result
    )
    assert_transform_equals(parsed, attribute_pattern_if_let_transformed)
    assert_typh_code_match_unparse(attribute_pattern_if_let_code)


attribute_pattern_positional_code = """
def f(r) {
    match (r) {
        case ({.x, .y = a}) {
            print(x, a)
        }
    }
}
"""
attribute_pattern_positional_result = """
def f(r):
    match r:
        case __attribute_pattern(x=x, y=a):
            print(x, a)
"""
attribute_pattern_positional_transformed = """
from typing import Final as _typh_bi_Final
from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol

@_typh_bi_runtime_checkable
class _typh_cl_f1_2_[_typh_tv_f1_0_x, _typh_tv_f1_1_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_f1_0_x]
    y: _typh_bi_Final[_typh_tv_f1_1_y]

def f(r):
    match r:
        case _typh_cl_f1_2_(x=x, y=a):
            print(x, a)
"""


def test_attribute_pattern_positional():
    parsed = assert_ast_equals(
        attribute_pattern_positional_code, attribute_pattern_positional_result
    )
    assert_transform_equals(parsed, attribute_pattern_positional_transformed)
    assert_typh_code_match_unparse(attribute_pattern_positional_code)
