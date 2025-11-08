from ..assertion_utils import assert_ast_equals, assert_ast_error, assert_ast_transform

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
    assert_ast_equals(while_let_none_check_code, while_let_none_check_result)


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
    assert_ast_equals(while_let_multiple_code, while_let_multiple_result)
    assert_ast_transform(while_let_multiple_code, while_let_multiple_transformed)
