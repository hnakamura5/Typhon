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
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class _typh_cl_m0_2_[_typh_tv_m0_0_x, _typh_tv_m0_1_y]:
    x: _typh_tv_m0_0_x
    y: _typh_tv_m0_1_y

    def __repr__(self):
        return f'{{|x={self.x!r}, y={self.y!r}|}}'
_typh_cl_m0_2_(x=1, y='2')
"""


def test_record_literal():
    parsed = assert_ast_equals(record_literal_code, record_literal_result)
    assert_transform_equals(parsed, record_literal_transformed)
