from ..assertion_utils import (
    assert_parse,
    assert_parse_first_error,
    assert_transform,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
)

while_let_none_check_code = """
var y: int? = None
while (let x = y) {
    print(x)
}
"""
while_let_none_check_result = """
y: (int,) = None
while True:
    match y:
        case x if x is not None:
            print(x)
        case _:
            pass
"""


def test_while_let_none_check():
    assert_parse(while_let_none_check_code, while_let_none_check_result)


while_let_multiple_code = """
from dataclasses import dataclass

@dataclass
class Point {
    var x: int
    var y: int
    var z: int
}

def func(point1: Point, point2: Point) -> int | None {
    while (let Point(x=a, y=b, z=c) = point1, Point(d, e, f) = point2; a > d) {
        print(a + b + c + d + e + f)
    } else {
        print("No match")
    }
    return None
}
"""
while_let_multiple_result = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:
    while True:
        match point1:
            case Point(x=a, y=b, z=c):
                match point2:
                    case Point(d, e, f) if a > d:
                        print(a + b + c + d + e + f)
                    case _:
                        pass
            case _:
                pass
    else:
        print('No match')
    return None
"""
while_let_multiple_transformed = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def func(point1: Point, point2: Point) -> int | None:
    _typh_vr_f2_0_ = True
    while _typh_vr_f2_0_:
        _typh_vr_f2_0_ = False
        match point1:
            case Point(x=a, y=b, z=c):
                match point2:
                    case Point(d, e, f) if a > d:
                        print(a + b + c + d + e + f)
                        _typh_vr_f2_0_ = True
                    case _:
                        pass
            case _:
                pass
    else:
        print('No match')
    return None
"""


def test_stmt_while_let_multiple():
    assert_parse(while_let_multiple_code, while_let_multiple_result)
    assert_transform(while_let_multiple_code, while_let_multiple_transformed)


while_let_parenless_code = """
var y: int? = None
while let x = y {
    print(x)
}
"""
while_let_parenless_result = """
y: (int,) = None
while True:
    match y:
        case x if x is not None:
            print(x)
        case _:
            pass
"""


def test_while_let_parenless():
    assert_parse_error_recovery(
        while_let_parenless_code,
        while_let_parenless_result,
        [
            ("expected '('", Range(Pos(2, 5), Pos(2, 6))),
            ("expected ')'", Range(Pos(2, 15), Pos(2, 16))),
        ],
    )


while_let_braceless_code = """
var y: int? = None
while let x = y
    print(x)
"""
while_let_braceless_result = """
y: (int,) = None
while True:
    match y:
        case x if x is not None:
            print(x)
        case _:
            pass
"""


def test_while_let_braceless():
    assert_parse_error_recovery(
        while_let_braceless_code,
        while_let_braceless_result,
        [
            ("expected '('", Range(Pos(2, 5), Pos(2, 6))),
            ("expected ')'", Range(Pos(2, 15), Pos(2, 16))),
            ("expected '{'", Range(Pos(3, 4), Pos(3, 5))),
            ("expected '}'", Range(Pos(3, 12), Pos(3, 13))),
        ],
    )
