from ..assertion_utils import assert_ast_equals, assert_ast_error, assert_ast_transform


if_let_none_check_code = """
var y: int? = None
if (let x = y) {
    print(x)
}
"""
if_let_none_check_result = """
y: (int,) = None
if True:
    match y:
        case x if x is not None:
            print(x)
"""
if_let_none_check_transformed = """
y: int | None = None
_typh_vr_m0_0_ = True
match y:
    case _typh_cn_m0_1_x if _typh_cn_m0_1_x is not None:
        print(_typh_cn_m0_1_x)
        _typh_vr_m0_0_ = False
"""


def test_if_let_none_check():
    assert_ast_equals(if_let_none_check_code, if_let_none_check_result)
    assert_ast_transform(if_let_none_check_code, if_let_none_check_transformed)


if_let_star_code = """
if (let (1, *rest) = (x, y, z)) {
    w = rest
}
"""
if_let_star_result = """
if True:
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
    if True:
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
    if True:
        match point:
            case Point(a, y=b, z=c) if a > 0:
                return a + b + c
    return None
"""


def test_stmt_if_let_class_keyword_pattern():
    assert_ast_equals(
        if_let_class_keyword_pattern_code, if_let_class_keyword_pattern_result
    )


if_let_multiple_code = """
from dataclasses import dataclass

@dataclass
class Point {
    var x: int
    var y: int
    var z: int
}

def func(point1: Point, point2: Point) -> int | None {
    if (let Point(x=a, y=b, z=c) = point1, Point(d, e, f) = point2; a > d) {
        print(a + b + c + d + e + f)
    } elif (let Point(a, b, c) = point1, Point(x=d, y=e, z=f) = point2) {
        return a + b + c + d + e + f
    } else {
        print("No match")
    }
    return None
}
"""
if_let_multiple_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:
    if True:
        match point1:
            case Point(x=a, y=b, z=c):
                match point2:
                    case Point(d, e, f) if a > d:
                        print(a + b + c + d + e + f)
    elif True:
        match point1:
            case Point(a, b, c):
                match point2:
                    case Point(x=d, y=e, z=f):
                        return a + b + c + d + e + f
    else:
        print('No match')
    return None
"""
if_let_multiple_transformed = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:
    _typh_vr_f2_1_ = True
    match point1:
        case Point(x=a, y=b, z=c):
            match point2:
                case Point(d, e, f) if a > d:
                    print(a + b + c + d + e + f)
                    _typh_vr_f2_1_ = False
    if _typh_vr_f2_1_:
        _typh_vr_f2_0_ = True
        match point1:
            case Point(a, b, c):
                match point2:
                    case Point(x=d, y=e, z=f):
                        return a + b + c + d + e + f
        if _typh_vr_f2_0_:
            print('No match')
    return None
"""


def test_stmt_if_let_multiple():
    assert_ast_equals(if_let_multiple_code, if_let_multiple_result)
    assert_ast_transform(if_let_multiple_code, if_let_multiple_transformed)


if_let_comma_error_code = """
def func(point: (int, int)) -> None {
    if (let a, b = point) { # Error: Comma without parentheses
        print(a + b)
    }
}
"""


def test_stmt_if_let_comma_error():
    assert_ast_error(if_let_comma_error_code, SyntaxError)


let_else_code = """
def func(x: int?) -> int {
    let y = x else {
        return 0
    }
    return y
}
"""
let_else_result = """
def func(x: (int,)) -> int:
    if True:
        match x:
            case y if y is not None:
    else:
        return 0
    return y
"""
let_else_transformed = """
def func(x: int | None) -> int:
    _typh_vr_f1_0_ = True
    match x:
        case y if y is not None:
            return y
    if _typh_vr_f1_0_:
        return 0
"""


def test_stmt_let_else():
    assert_ast_equals(let_else_code, let_else_result)
    assert_ast_transform(let_else_code, let_else_transformed)
