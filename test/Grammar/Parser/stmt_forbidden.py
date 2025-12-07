from ..assertion_utils import assert_transform_first_error, assert_transform_errors
from ....src.Typhon.Grammar.syntax_errors import ForbiddenStatementError


stmt_code_error_code = """
var x = 10;
del x;
"""


def test_stmt_del_error():
    assert_transform_first_error(
        stmt_code_error_code,
        ForbiddenStatementError,
        "`del` statement is forbidden",
    )


stmt_global_error_code = """
var x = 10;
def f() {
    global x;
    x = 20;
}
"""


def test_stmt_global_error():
    assert_transform_first_error(
        stmt_global_error_code,
        ForbiddenStatementError,
        "`global` statement is forbidden",
    )


stmt_nonlocal_error_code = """
def f() {
    var x = 10;
    def g() {
        nonlocal x;
        x = 20;
    }
}
"""


def test_stmt_nonlocal_error():
    assert_transform_first_error(
        stmt_nonlocal_error_code,
        ForbiddenStatementError,
        "`nonlocal` statement is forbidden",
    )


stmt_import_wildcard_error_code = """
from math import *;
print(sin(0));
"""


def test_stmt_import_wildcard_error():
    assert_transform_first_error(
        stmt_import_wildcard_error_code,
        ForbiddenStatementError,
        "Wildcard import is forbidden",
    )


stmt_if_in_class_error_code = """
class A {
    if (True) {
        print("Hello");
    }
}
"""


def test_stmt_control_in_class_error():
    assert_transform_first_error(
        stmt_if_in_class_error_code,
        ForbiddenStatementError,
        "inside class definition",
    )


stmt_for_in_class_error_code = """
class A {
    for (let i in range(10)) {
        print(i);
    }
}
"""


def test_stmt_for_in_class_error():
    assert_transform_first_error(
        stmt_for_in_class_error_code,
        ForbiddenStatementError,
        "inside class definition",
    )


multi_assign_in_class_error_code = """
class A {
    var x = 10, y = 20;
}
"""


def test_multi_assign_in_class_error():
    assert_transform_first_error(
        multi_assign_in_class_error_code,
        ForbiddenStatementError,
        "inside class definition",
    )


unpack_assign_in_class_error_code = """
class A {
    var (x, y) = (10, 20);
}
"""


def test_unpack_assign_in_class_error():
    assert_transform_first_error(
        unpack_assign_in_class_error_code,
        ForbiddenStatementError,
        "inside class definition",
    )


inline_with_top_level_error_code = """
with let x = open('file.txt')
"""


def test_inline_with_top_level_error():
    assert_transform_first_error(
        inline_with_top_level_error_code,
        ForbiddenStatementError,
        "module top level",
    )


inline_async_with_top_level_error_code = """
async with let x = open('file.txt')
"""


def test_inline_async_with_top_level_error():
    assert_transform_first_error(
        inline_async_with_top_level_error_code,
        ForbiddenStatementError,
        "module top level",
    )


let_else_top_level_error_code = """
let x = 10 else {
    raise ValueError()
}
"""


def test_let_else_top_level_error():
    assert_transform_first_error(
        let_else_top_level_error_code,
        ForbiddenStatementError,
        "module top level",
    )


multiple_errors_code = """
var x = 10;
del x;
def f() {
    global x;
    x = 20;
    from math import *;
}
"""


def test_multiple_forbidden_statement_errors():
    assert_transform_errors(
        multiple_errors_code,
        [
            ForbiddenStatementError,  # for del
            ForbiddenStatementError,  # for global
            ForbiddenStatementError,  # for wildcard import
        ],
    )
