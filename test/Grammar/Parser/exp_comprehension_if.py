from ..assertion_utils import (
    assert_parse,
    assert_transform_ast,
    assert_typh_code_match_unparse,
)


comp_if_code = """
let val = (if (True) 1 else 0)
"""
comp_if_result = """
val = 1 if True else 0
"""


def test_comp_if():
    assert_parse(comp_if_code, comp_if_result)
    assert_typh_code_match_unparse(comp_if_code)


comp_if_nested_code = """
let val = (if (True) 1 elif (False) (if (True) 2 else 3) else -1)
"""
comp_if_nested_result = """
val = 1 if True else (2 if True else 3) if False else -1
"""


def test_comp_if_nested():
    assert_parse(comp_if_nested_code, comp_if_nested_result)
    assert_typh_code_match_unparse(comp_if_nested_code)


comp_if_then_only_code = """
let val = (if (True) 1)
"""
comp_if_then_only_result = """
val = 1 if True else None
"""


def test_comp_if_then_only():
    assert_parse(comp_if_then_only_code, comp_if_then_only_result)
    assert_typh_code_match_unparse(comp_if_then_only_code)


comp_if_let_code = """
def func(a: int?) -> int? {
    return (if (let a = a) a else None)
}
"""
comp_if_let_result = """
def func(a: (int,)) -> (int,):
    return __if_let_comp
"""
comp_if_let_transformed = """
from typing import Final as _typh_bi_Final

def func(a: int | None) -> int | None:

    def _typh_cc_f1_0():
        match a:
            case _typh_cn_f2_0_a if _typh_cn_f2_0_a is not None:
                _typh_cn_f2_0_a: _typh_bi_Final
                return _typh_cn_f2_0_a
            case _:
                pass
        return None
    return _typh_cc_f1_0()
"""


def test_comp_if_let():
    parsed = assert_parse(comp_if_let_code, comp_if_let_result)
    assert_transform_ast(parsed, comp_if_let_transformed)
    assert_typh_code_match_unparse(comp_if_let_code)


comp_if_let_multiple_code = """
from dataclasses import dataclass

@dataclass
class Point {
    var x: int
    var y: int
    var z: int
}

def func(point1: Point, point2: Point) -> int | None {
    return (if (let Point(x=a, y=b, z=c) = point1, Point(d, e, f) = point2; a > d)
                a + b + c + d + e + f
            elif (let Point(a, b, c) = point1, Point(x=d, y=e, z=f) = point2)
                a + b + c + d + e + f)
}
"""
comp_if_let_multiple_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:
    return __if_let_comp
"""
comp_if_let_multiple_transformed = """
from typing import Final as _typh_bi_Final
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:

    def _typh_cc_f2_0():
        match point1:
            case Point(x=a, y=b, z=c):
                a: _typh_bi_Final
                b: _typh_bi_Final
                c: _typh_bi_Final
                match point2:
                    case Point(d, e, f) if a > d:
                        d: _typh_bi_Final
                        e: _typh_bi_Final
                        f: _typh_bi_Final
                        return a + b + c + d + e + f
                    case _:
                        pass
            case _:
                pass

        def _typh_cc_f3_0():
            match point1:
                case Point(a, b, c):
                    a: _typh_bi_Final
                    b: _typh_bi_Final
                    c: _typh_bi_Final
                    match point2:
                        case Point(x=d, y=e, z=f):
                            d: _typh_bi_Final
                            e: _typh_bi_Final
                            f: _typh_bi_Final
                            return a + b + c + d + e + f
                        case _:
                            pass
                case _:
                    pass
        return _typh_cc_f3_0()
    return _typh_cc_f2_0()
"""


def test_comp_if_let_multiple():
    parsed = assert_parse(comp_if_let_multiple_code, comp_if_let_multiple_result)
    assert_transform_ast(parsed, comp_if_let_multiple_transformed)
    assert_typh_code_match_unparse(comp_if_let_multiple_code)
