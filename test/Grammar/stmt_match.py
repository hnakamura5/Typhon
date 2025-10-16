from ..assertion_utils import (
    assert_ast_equals,
    assert_ast_error,
    assert_transform_equals,
)

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


match_annot_code = """
def func(x: (int, str)) -> int {
    match (x) {
        case (a: int, b: str) {
            return a + len(b)
        }
        case (a: str) {
            return a
        }
    }
    return 0
}
"""
match_annot_result = """
def func(x: (int, str)) -> int:
    match x:
        case [a, b]:
            return a + len(b)
        case a:
            return a
    return 0
"""
match_annot_transformed = """
def func(x: tuple[int, str]) -> int:
    _typh_cn_f1_0_a: int
    _typh_cn_f1_1_b: str
    _typh_cn_f1_2_a: str
    match x:
        case [_typh_cn_f1_0_a, _typh_cn_f1_1_b]:
            return _typh_cn_f1_0_a + len(_typh_cn_f1_1_b)
        case _typh_cn_f1_2_a:
            return _typh_cn_f1_2_a
    return 0
"""


def test_stmt_match_annot():
    parsed = assert_ast_equals(match_annot_code, match_annot_result)
    assert_transform_equals(parsed, match_annot_transformed)


match_sequence_annot_code = """
def func(x: [int]) -> int {
    match (x) {
        case ([a: int, b: int]) {
            return a + b
        }
        case ([a: int, b: int, c: int, *rest: [int]]) {
            return a + b + c + sum(rest)
        }
    }
    return 0
}
"""
match_sequence_annot_result = """
def func(x: [int]) -> int:
    match x:
        case [a, b]:
            return a + b
        case [a, b, c, *rest]:
            return a + b + c + sum(rest)
    return 0
"""
match_sequence_annot_transformed = """
def func(x: list[int]) -> int:
    _typh_cn_f1_0_a: int
    _typh_cn_f1_1_b: int
    _typh_cn_f1_2_a: int
    _typh_cn_f1_3_b: int
    _typh_cn_f1_4_c: int
    _typh_cn_f1_5_rest: list[int]
    match x:
        case [_typh_cn_f1_0_a, _typh_cn_f1_1_b]:
            return _typh_cn_f1_0_a + _typh_cn_f1_1_b
        case [_typh_cn_f1_2_a, _typh_cn_f1_3_b, _typh_cn_f1_4_c, *_typh_cn_f1_5_rest]:
            return _typh_cn_f1_2_a + _typh_cn_f1_3_b + _typh_cn_f1_4_c + sum(_typh_cn_f1_5_rest)
    return 0
"""


def test_stmt_match_sequence_annot():
    parsed = assert_ast_equals(match_sequence_annot_code, match_sequence_annot_result)
    assert_transform_equals(parsed, match_sequence_annot_transformed)
