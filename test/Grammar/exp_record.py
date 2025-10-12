from ..assertion_utils import (
    assert_ast_equals,
    assert_transform_equals,
)
import ast


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
from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol
from typing import Final as _typh_bi_Final
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
