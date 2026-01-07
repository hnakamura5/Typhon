from ..assertion_utils import assert_transform, assert_transform_first_error
from src.Typhon.Grammar.syntax_errors import ScopeError

tdz_code = """
def f() {
    g(x);
}

var x = 10;

def g(y) {
    print(x + y);
}
f()
"""
tdz_result = """
def f():
    g(x)
x = 10

def g(y):
    print(x + y)
f()
"""


def test_tdz():
    assert_transform(tdz_code, tdz_result)


# Violation of TDZ in function call f() before declaration of g
tdz_violation_error_code = """
def f() {
    g(x);
}

var x = 10;
f()

def g(y) {
    print(x + y);
}
"""


def test_tdz_violation_error():
    assert_transform_first_error(
        tdz_violation_error_code,
        ScopeError,
        "'f' is accessed in its temporal dead zone",
    )


tdz_class_code = """
class A {
    def f() {
        g(x);
    }
}

var x = 10;

def g(y) {
    print(x + y);
}

let a = A();
"""
tdz_class_result = """
class A:

    def f(self):
        g(x)
x = 10

def g(y):
    print(x + y)
a = A()
"""


def test_tdz_class():
    assert_transform(tdz_class_code, tdz_class_result)


tdz_violation_class_error_code = """
class A {
    def f() {
        g(x);
    }
}

var x = 10;

let a = A();
def g(y) {
    print(x + y);
}
"""


def test_tdz_violation_class_error():
    assert_transform_first_error(
        tdz_violation_class_error_code,
        ScopeError,
        "'A' is accessed in its temporal dead zone",
    )


tdz_mutation_code = """
def f() {
    x = 20
}
var x = 10;
f()
"""
tdz_mutation_result = """
def f():
    global x
    x = 20
x = 10
f()
"""


def test_tdz_mutation():
    assert_transform(tdz_mutation_code, tdz_mutation_result)


tdz_mutation_violation_error_code = """
def f() {
    x = 20
}
f()
var x = 10;
"""


def test_tdz_mutation_violation_error():
    assert_transform_first_error(
        tdz_mutation_violation_error_code,
        ScopeError,
        "'f' is accessed in its temporal dead zone",
    )


tdz_shadow_code = """
def f() {
    x = x + 1;
    let x = x + 1;
    return x;
}
var x = 10;
f()
"""
tdz_shadow_result = """
def f():
    global x
    x = x + 1
    _typh_cn_f1_0_x = x + 1
    return _typh_cn_f1_0_x
x = 10
f()
"""


def test_tdz_shadow():
    assert_transform(tdz_shadow_code, tdz_shadow_result)


tdz_shadow_violation_error_code = """
def f() {
    x = x + 1;
    let x = x + 1;
    return x;
}
f()
var x = 10;
"""


def test_tdz_shadow_violation_error():
    assert_transform_first_error(
        tdz_shadow_violation_error_code,
        ScopeError,
        "'f' is accessed in its temporal dead zone",
    )


tdz_mutual_recursion_code = """
def f() {
    g(x);
}

def g(y) {
    f();
}

var x = 10;
f()
"""
tdz_mutual_recursion_result = """
def f():
    g(x)

def g(y):
    f()
x = 10
f()
"""


def test_tdz_mutual_recursion():
    assert_transform(tdz_mutual_recursion_code, tdz_mutual_recursion_result)


tdz_violation_mutual_recursion_error_code = """
def f() {
    g(x);
}

def g(y) {
    f();
}

f()
var x = 10;
"""


def test_tdz_violation_mutual_recursion_error():
    assert_transform_first_error(
        tdz_violation_mutual_recursion_error_code,
        ScopeError,
        "'f' is accessed in its temporal dead zone",
    )
