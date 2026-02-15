from ...assertion_utils import (
    assert_typh_code_match_unparse,
    assert_transform,
    SourceMapAsserter,
)
from Typhon.SourceMap.datatype import Range, Pos
from Typhon.Driver.debugging import set_debug_verbose


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
from typing import Final as _typh_bi_Final

def left_func(x: int) -> int:
    y = 0
    for i in range(x):
        i: _typh_bi_Final
        if i % 2 == 0:
            y += i
    return y
"""


def test_match_typhon_stmt_if():
    assert_transform(code_stmt_if, transformed_code_stmt_if)
    assert_typh_code_match_unparse(code_stmt_if)
    sa = SourceMapAsserter(code_stmt_if)
    sa.assert_range_text(  # left_func (defined name of FunctionDef)
        Range(Pos(1, 4), Pos(1, 13)),
        "left_func",
        Range(Pos(2, 4), Pos(2, 13)),
        "left_func",
    )
    sa.assert_range(  # x: int
        Range(start=Pos(1, 13), end=Pos(1, 19)),
        Range(start=Pos(2, 13), end=Pos(2, 19)),
    )
    sa.assert_range(  # var y = 0
        Range(start=Pos(2, 4), end=Pos(2, 13)),
        Range(start=Pos(3, 4), end=Pos(3, 9)),
    )


code_def = """
from decorators import my_decorator

@my_decorator
def
left_func(x: int) -> int {
    return x + 1
}
"""
transformed_code_def = """
from decorators import my_decorator

@my_decorator
def left_func(x: int) -> int:
    return x + 1
"""


def test_match_typhon_stmt_def():
    assert_transform(code_def, transformed_code_def)
    assert_typh_code_match_unparse(code_def)

    sa = SourceMapAsserter(code_def)
    sa.assert_range_text(  # my_decorator (defined name of import)
        Range(Pos(1, 23), Pos(1, 35)),
        "my_decorator",
        Range(Pos(0, 23), Pos(0, 35)),
        "my_decorator",
    )
    sa.assert_range_text(  # left_func (defined name of FunctionDef)
        Range(Pos(5, 0), Pos(5, 9)),
        "left_func",
        Range(Pos(3, 4), Pos(3, 13)),
        "left_func",
    )


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


code_import_from = """
from ...SourceMap.matching.python_exp import test_match_python_arithmetic
"""


def test_match_typhon_stmt_import_from():
    assert_typh_code_match_unparse(code_import_from)
    sa = SourceMapAsserter(code_import_from)
    sa.assert_range_text(  # import from module "SourceMap"
        Range(Pos(1, 8), Pos(1, 17)),
        "SourceMap",
        Range(Pos(0, 8), Pos(0, 17)),
        "SourceMap",
    )
    sa.assert_range_text(  # import from module "matching"
        Range(Pos(1, 18), Pos(1, 26)),
        "matching",
        Range(Pos(0, 18), Pos(0, 26)),
        "matching",
    )
    sa.assert_range_text(  # test_match_python_arithmetic (defined name of import)
        Range(Pos(1, 45), Pos(1, 73)),
        "test_match_python_arithmetic",
        Range(Pos(0, 45), Pos(0, 73)),
        "test_match_python_arithmetic",
    )
