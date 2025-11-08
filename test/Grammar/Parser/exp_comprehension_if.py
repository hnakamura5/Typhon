from ..assertion_utils import assert_ast_equals, assert_transform_equals


comp_if_code = """
let val = (if (True) 1 else 0)
"""
comp_if_result = """
val = 1 if True else 0
"""


def test_comp_if():
    assert_ast_equals(comp_if_code, comp_if_result)


comp_if_nested_code = """
let val = (if (True) 1 elif (False) (if (True) 2 else 3) else -1)
"""
comp_if_nested_result = """
val = 1 if True else (2 if True else 3) if False else -1
"""


def test_comp_if_nested():
    assert_ast_equals(comp_if_nested_code, comp_if_nested_result)


comp_if_then_only_code = """
let val = (if (True) 1)
"""
comp_if_then_only_result = """
val = 1 if True else None
"""


def test_comp_if_then_only():
    assert_ast_equals(comp_if_then_only_code, comp_if_then_only_result)


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
def func(a: int | None) -> int | None:

    def _typh_cc_f1_0():
        match a:
            case _typh_cn_f2_0_a if _typh_cn_f2_0_a is not None:
                return _typh_cn_f2_0_a
            case _:
                pass
        return None
    return _typh_cc_f1_0()
"""


def test_comp_if_let():
    parsed = assert_ast_equals(comp_if_let_code, comp_if_let_result)
    assert_transform_equals(parsed, comp_if_let_transformed)


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
                match point2:
                    case Point(d, e, f) if a > d:
                        return a + b + c + d + e + f
                    case _:
                        pass
            case _:
                pass

        def _typh_cc_f3_0():
            match point1:
                case Point(a, b, c):
                    match point2:
                        case Point(x=d, y=e, z=f):
                            return a + b + c + d + e + f
                        case _:
                            pass
                case _:
                    pass
        return _typh_cc_f3_0()
    return _typh_cc_f2_0()
"""


def test_comp_if_let_multiple():
    parsed = assert_ast_equals(comp_if_let_multiple_code, comp_if_let_multiple_result)
    assert_transform_equals(parsed, comp_if_let_multiple_transformed)
