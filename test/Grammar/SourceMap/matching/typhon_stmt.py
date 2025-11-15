from ...assertion_utils import (
    assert_typh_code_match_unparse,
    assert_ast_transform,
    SourceMapAsserter,
)
from .....src.Typhon.SourceMap.datatype import Range, Pos


code_stmt_if = """
def left_func(x: int) -> int {
    var y = 0;
    for (let i in range(x)) {
        if (i % 2 == 0) {
            y += i;
        }
    }
    return y;
}
"""
transformed_code_stmt_if = """
def left_func(x: int) -> int:
    y = 0
    for i in range(x):
        if i % 2 == 0:
            y += i
    return y
"""


def test_match_typhon_stmt_if():
    assert_ast_transform(code_stmt_if, transformed_code_stmt_if)
    assert_typh_code_match_unparse(code_stmt_if)
    sa = SourceMapAsserter(code_stmt_if)
    sa.assert_range(  # left_func (part of FunctionDef)
        Range(Pos(2, 4), Pos(2, 13)),
        Range(Pos(1, 4), Pos(1, 13)),
    )
    sa.assert_range(  # x: int
        Range(start=Pos(2, 14), end=Pos(2, 20)),
        Range(start=Pos(1, 14), end=Pos(1, 20)),
    )
    sa.assert_range(  # var y = 0
        Range(start=Pos(3, 4), end=Pos(3, 13)),
        Range(start=Pos(2, 4), end=Pos(2, 9)),
    )

    # TODO: e.g. "left_func" is only included in FunctionDef. The range is of course whole function. How to match such a thing?


code_stmt_nested_func = """
def left_func(x: int) -> int {
    def nested_func1(y: int) -> int {
        return y * 2;
    }

    def nested_func2(z: int) -> int {
        return z + 3;
    }

    return nested_func1(x) + nested_func2(x);
}
"""


def test_match_typhon_stmt_nested_func():
    assert_typh_code_match_unparse(code_stmt_nested_func)


code_stmt_class_with_method = """
class A {
    def method1(x: int) -> int {
        return x + 1;
    }

    def method2(y: int) -> int {
        return y * 2;
    }
}
"""


def test_match_typhon_stmt_class_with_method():
    assert_typh_code_match_unparse(code_stmt_class_with_method)


code_stmt_try_except = """
def left_func(x: int) -> int {
    try {
        return 10 // x;
    } except (ZeroDivisionError as e) {
        return 0;
    }
}
"""


def test_match_typhon_stmt_try_except():
    assert_typh_code_match_unparse(code_stmt_try_except)


code_stmt_with = """
def left_func(file_path: str) -> str {
    with (let f = open(file_path, "r")) {
        let content = f.read();
        return content;
    }
}
"""


def test_match_typhon_stmt_with():
    assert_typh_code_match_unparse(code_stmt_with)


code_stmt_if_let = """
def left_func(opt_x: int?, opt_y: int?) -> int {
    if (let x = opt_x, y = opt_y; x > 0) {
        return x + 1;
    } else {
        return 0;
    }
}
"""


def test_match_typhon_stmt_if_let():
    assert_typh_code_match_unparse(code_stmt_if_let)


code_stmt_let_else = """
def left_func(opt_x: int?) -> int {
    let x = opt_x else {
        return 0
    }
    return x + 1
}
"""


def test_match_typhon_stmt_let_else():
    assert_typh_code_match_unparse(code_stmt_let_else)


code_while_let_multiple_code = """
def func(point1: (int?, int), point2: (int?, int)) -> int? {
    while (let (a, 1) = point1) {
        while (let (c, 2) = point2; a > c) {
            print(a + c)
        }
    }
    else {
        print("No match")
    }
    return None
}
"""


def test_match_typhon_stmt_while_let_multiple():
    assert_typh_code_match_unparse(code_while_let_multiple_code)
