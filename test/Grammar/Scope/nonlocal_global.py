from ..assertion_utils import assert_transform, assert_transform_first_error
from src.Typhon.Grammar.syntax_errors import ScopeError


global_var_code = """
var x = 10;
def f() {
    x = 20;
}
f();
print(x);
"""

global_var_result = """
x = 10

def f():
    global x
    x = 20
f()
print(x)
"""


def test_global_var():
    assert_transform(global_var_code, global_var_result)


global_var_ref_code = """
var x = 10;
def f() {
    print(x);
}
f();
"""
global_var_ref_result = """
x = 10

def f():
    print(x)
f()
"""


def test_global_var_ref():
    assert_transform(global_var_ref_code, global_var_ref_result)


global_let_error_code = """
let x = 10;
def f() {
    x = 20;
}
f();
print(x);
"""


def test_global_let_error():
    assert_transform_first_error(
        global_let_error_code, ScopeError, "assign to immutable"
    )


nonlocal_var_code = """
def f() {
    var x = 10;
    def g() {
        x = 20;
    }
    g();
    print(x);
}
f();
"""

nonlocal_var_result = """
def f():
    x = 10

    def g():
        nonlocal x
        x = 20
    g()
    print(x)
f()
"""


def test_nonlocal_var():
    assert_transform(nonlocal_var_code, nonlocal_var_result)


nonlocal_var_ref_code = """
def f() {
    var x = 10;
    def g() {
        print(x);
    }
    g();
}
f();
"""
nonlocal_var_ref_result = """
def f():
    x = 10

    def g():
        print(x)
    g()
f()
"""


def test_nonlocal_var_ref():
    assert_transform(nonlocal_var_ref_code, nonlocal_var_ref_result)


nonlocal_let_error_code = """
def f() {
    let x = 10;
    def g() {
        x = 20;
    }
    g();
    print(x);
}
f();
"""


def test_nonlocal_let_error():
    assert_transform_first_error(
        nonlocal_let_error_code, ScopeError, "assign to immutable"
    )
