from ..assertion_utils import (
    assert_parse,
    assert_parse_error,
    assert_transform,
    assert_typh_code_match_unparse,
)
from ....src.Typhon.Driver.debugging import set_debug_mode, set_debug_verbose


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
        case _:
            pass
"""
if_let_none_check_transformed = """
y: int | None = None
_typh_vr_m0_0_ = True
match y:
    case _typh_cn_m0_1_x if _typh_cn_m0_1_x is not None:
        _typh_vr_m0_0_ = False
        print(_typh_cn_m0_1_x)
    case _:
        pass
"""


def test_if_let_none_check():
    assert_parse(if_let_none_check_code, if_let_none_check_result)
    assert_transform(if_let_none_check_code, if_let_none_check_transformed)
    assert_typh_code_match_unparse(if_let_none_check_code)


if_let_star_code = """
def func(x: int, y: int, z: int) {
    if (let [1, *rest] = (x, y, z)) {
        return rest
    }
}
"""
if_let_star_result = """
def func(x: int, y: int, z: int):
    if True:
        match (x, y, z):
            case [1, *rest]:
                return rest
            case _:
                pass
"""
if_let_star_transformed = """
def func(x: int, y: int, z: int):
    match (x, y, z):
        case [1, *rest]:
            return rest
        case _:
            pass
"""


def test_stmt_if_let_star():
    assert_parse(if_let_star_code, if_let_star_result)
    assert_transform(if_let_star_code, if_let_star_transformed)
    assert_typh_code_match_unparse(if_let_star_code)


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
            case _:
                pass
    return None
"""


def test_stmt_if_let_class_code():
    assert_parse(if_let_class_code, if_let_class_result)
    assert_typh_code_match_unparse(if_let_class_code)


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
            case _:
                pass
    return None
"""


def test_stmt_if_let_class_keyword_pattern():
    assert_parse(if_let_class_keyword_pattern_code, if_let_class_keyword_pattern_result)
    assert_typh_code_match_unparse(if_let_class_keyword_pattern_code)


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
                    case _:
                        pass
            case _:
                pass
    elif True:
        match point1:
            case Point(a, b, c):
                match point2:
                    case Point(x=d, y=e, z=f):
                        return a + b + c + d + e + f
                    case _:
                        pass
            case _:
                pass
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
    _typh_vr_f2_0_ = True
    match point1:
        case Point(x=a, y=b, z=c):
            match point2:
                case Point(d, e, f) if a > d:
                    _typh_vr_f2_0_ = False
                    print(a + b + c + d + e + f)
                case _:
                    pass
        case _:
            pass
    if _typh_vr_f2_0_:
        match point1:
            case Point(a, b, c):
                match point2:
                    case Point(x=d, y=e, z=f):
                        return a + b + c + d + e + f
                    case _:
                        pass
            case _:
                pass
        print('No match')
    return None
"""


def test_stmt_if_let_multiple():
    assert_parse(if_let_multiple_code, if_let_multiple_result)
    assert_transform(if_let_multiple_code, if_let_multiple_transformed)
    assert_typh_code_match_unparse(if_let_multiple_code)


if_let_comma_error_code = """
def func(point: (int, int)) -> None {
    if (let a, b = point) { # Error: Comma without parentheses
        print(a + b)
    }
}
"""


def test_stmt_if_let_comma_error():
    assert_parse_error(if_let_comma_error_code, SyntaxError)


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
            case _:
                pass
    else:
        return 0
    return y
"""
let_else_transformed = """
def func(x: int | None) -> int:
    match x:
        case y if y is not None:
            return y
        case _:
            pass
    return 0
"""


def test_stmt_let_else():
    assert_parse(let_else_code, let_else_result)
    assert_transform(let_else_code, let_else_transformed)
    assert_typh_code_match_unparse(let_else_code)


let_else_with_code = """
def func(x: int) -> int {
    let i = (try 2 // x) else {
        return -1
    }
    with let f = open('file.txt')
    f.write(str(i))
    return i
}
"""
let_else_with_result = """
def func(x: int) -> int:
    if True:
        match __try_comp:
            case i if i is not None:
            case _:
                pass
    else:
        return -1
    with open('file.txt') as f:
    f.write(str(i))
    return i
"""
let_else_with_transformed = """
def func(x: int) -> int:

    def _typh_cc_f1_0():
        try:
            return 2 // x
        except:
            return None
    match _typh_cc_f1_0():
        case i if i is not None:
            with open('file.txt') as f:
                f.write(str(i))
                return i
        case _:
            pass
    return -1
"""


def test_stmt_let_else_with():
    assert_parse(let_else_with_code, let_else_with_result)
    assert_transform(let_else_with_code, let_else_with_transformed)
    assert_typh_code_match_unparse(let_else_with_code)


let_else_annotation_code = """
def func(x: int?) -> int {
    let y: int = x else {
        return 0
    }
    return y
}
"""
let_else_annotation_result = """
def func(x: (int,)) -> int:
    if True:
        match x:
            case y if y is not None:
            case _:
                pass
    else:
        return 0
    return y
"""
let_else_annotation_transformed = """
def func(x: int | None) -> int:
    _typh_cn_f1_0_y: int
    match x:
        case _typh_cn_f1_0_y if _typh_cn_f1_0_y is not None:
            return _typh_cn_f1_0_y
        case _:
            pass
    return 0
"""


def test_stmt_let_else_annotation():
    assert_parse(let_else_annotation_code, let_else_annotation_result)
    assert_transform(let_else_annotation_code, let_else_annotation_transformed)
    assert_typh_code_match_unparse(let_else_annotation_code)
