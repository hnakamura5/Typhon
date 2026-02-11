from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)

match_comp_code = """
from dataclasses import dataclass

@dataclass
class Point {
    let x: int
    let y: int
}

def func(point: Point) -> int | None {
    return (match (point) case (Point(a, b)) a + b)
}
"""
match_comp_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def func(point: Point) -> int | None:
    return __match_comp
"""
match_comp_transformed = """
from typing import Final as _typh_bi_Final
from dataclasses import dataclass

@dataclass
class Point:
    x: _typh_bi_Final[int]
    y: _typh_bi_Final[int]

def func(point: Point) -> int | None:

    def _typh_cc_f2_0():
        match point:
            case Point(a, b):
                a: _typh_bi_Final
                b: _typh_bi_Final
                return a + b
        return None
    return _typh_cc_f2_0()
"""


def test_comp_match():
    parsed = assert_parse(match_comp_code, match_comp_result)
    assert_transform_ast(parsed, match_comp_transformed)
    assert_typh_code_match_unparse(match_comp_code)


match_comp_guard_code = """
from dataclasses import dataclass

@dataclass
class Point {
    let x: int
    let y: int
}
def func(point: Point) -> int | None {
    return (match (point)
                case (Point(a, b)) if (a > 0) a + b
                case (Point(a, b)) a - b)
}
"""
match_comp_guard_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def func(point: Point) -> int | None:
    return __match_comp
"""
match_comp_guard_transformed = """
from typing import Final as _typh_bi_Final
from dataclasses import dataclass

@dataclass
class Point:
    x: _typh_bi_Final[int]
    y: _typh_bi_Final[int]

def func(point: Point) -> int | None:

    def _typh_cc_f2_0():
        match point:
            case Point(a, b) if a > 0:
                a: _typh_bi_Final
                b: _typh_bi_Final
                return a + b
            case Point(a, b):
                a: _typh_bi_Final
                b: _typh_bi_Final
                return a - b
        return None
    return _typh_cc_f2_0()
"""


def test_comp_match_guard():
    parsed = assert_parse(match_comp_guard_code, match_comp_guard_result)
    assert_transform_ast(parsed, match_comp_guard_transformed)
    assert_typh_code_match_unparse(match_comp_guard_code)
