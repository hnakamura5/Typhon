from ..assertion_utils import assert_ast_equals, assert_ast_error

match_code = """
match (x) {
    case (1) {
        y = 1
    } case (2) {
        y = 2
    }
}
"""
match_result = """
match x:
    case 1:
        y = 1
    case 2:
        y = 2
"""


def test_stmt_match():
    assert_ast_equals(match_code, match_result)


match_with_guard_code = """
match (x) {
    case (1) if (y == 1) {
        z = 1
    }
    case (2) if (y == 2) {
        z = 2
    }
}
"""
match_with_guard_result = """
match x:
    case 1 if y == 1:
        z = 1
    case 2 if y == 2:
        z = 2
"""


def test_stmt_match_with_guard():
    assert_ast_equals(match_with_guard_code, match_with_guard_result)


match_sequence_code = """
match (x, y) {
    case (1, 2) {
        z = 1
    } case (2, 3) {
        z = 2
    }
}
"""
match_sequence_result = """
match (x, y):
    case [1, 2]:
        z = 1
    case [2, 3]:
        z = 2
"""
# Sequence is pattern printed using '[' and ']' by unparse.
# No semantic difference between '()' and '[]' in this pattern.


def test_stmt_match_sequence():
    assert_ast_equals(match_sequence_code, match_sequence_result)


match_star_code = """
match (x, y, z) {
    case (1, *rest) {
        w = rest
    }
}
"""
match_star_result = """
match (x, y, z):
    case [1, *rest]:
        w = rest
"""


def test_stmt_match_star():
    assert_ast_equals(match_star_code, match_star_result)


match_star_error_code = """
match (x, y, z) {
    case (*rest) {
        w = rest
    }
}
"""


# TODO: Make this message better.
def test_stmt_match_star_error():
    assert_ast_error(match_star_error_code, SyntaxError)


match_class_code = """
from dataclasses import dataclass

@dataclass
class Point {
    let x: int
    let y: int
}

def func(point: Point) -> int | None {
    match (point) {
        case (Point(a, b)) {
            return a + b
        }
    }
    return None
}
"""
match_class_result = """
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


def test_stmt_match_class_code():
    assert_ast_equals(match_class_code, match_class_result)


match_class_keyword_pattern_code = """
from dataclasses import dataclass

@dataclass
class Point {
    var x: int
    var y: int
    var z: int
}

def func(point: Point) -> int | None {
    match (point) {
        case (Point(a, y=b, z=c)) if (a > 0) {
            return a + b + c
        }
    }
    return None
}
"""
match_class_keyword_pattern_result = """
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


def test_stmt_match_class_keyword_pattern():
    assert_ast_equals(
        match_class_keyword_pattern_code, match_class_keyword_pattern_result
    )
