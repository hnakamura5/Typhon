from ..assertion_utils import assert_ast_equals


if_let_none_check_code = """
var y: int? = None
if (let x = y) {
    print(x)
}
"""
if_let_none_check_result = """
y: (int,) = None
match y:
    case x if x is not None:
        print(x)
"""


def test_if_let_none_check():
    assert_ast_equals(if_let_none_check_code, if_let_none_check_result)


if_let_star_code = """
if (let (1, *rest) = (x, y, z)) {
    w = rest
}
"""
if_let_star_result = """
match (x, y, z):
    case [1, *rest]:
        w = rest
"""


def test_stmt_if_let_star():
    assert_ast_equals(if_let_star_code, if_let_star_result)


if_let_class_code = """
from dataclasses import dataclass

@dataclass
class Point {
    let x: int
    let y: int
}

def func(point: Point) -> int | None {
    if (let Point(a, b) = point) {
        return a + b
    }
    return None
}
"""
if_let_class_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def func(point: Point) -> int | None:
    match point:
        case Point(a, b):
            return a + b
    return None
"""


def test_stmt_if_let_class_code():
    assert_ast_equals(if_let_class_code, if_let_class_result)


if_let_class_keyword_pattern_code = """
from dataclasses import dataclass

@dataclass
class Point {
    var x: int
    var y: int
    var z: int
}

def func(point: Point) -> int | None {
    if (let Point(a, y=b, z=c) = point; a > 0) {
        return a + b + c
    }
    return None
}
"""
if_let_class_keyword_pattern_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point: Point) -> int | None:
    match point:
        case Point(a, y=b, z=c) if a > 0:
            return a + b + c
    return None
"""


def test_stmt_if_let_class_keyword_pattern():
    assert_ast_equals(
        if_let_class_keyword_pattern_code, if_let_class_keyword_pattern_result
    )
