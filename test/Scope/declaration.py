from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Typhon.Grammar.syntax_errors import ScopeError

decl_var_code = """
var x = 10;
x = x + 5;
print(x);
"""
decl_var_result = """
x = 10
x = x + 5
print(x)
"""


def test_decl_var():
    assert_ast_transform(decl_var_code, decl_var_result)


decl_immutable_error_code = """
let y = 20;
y = y + 5;
"""


def test_decl_immutable_error():
    assert_transform_error(decl_immutable_error_code, ScopeError, "assign to immutable")


decl_duplicate_error_code = """
var z = 30;
var z = 40;
"""


def test_decl_duplicate_error():
    assert_transform_error(decl_duplicate_error_code, ScopeError, "already declared")


decl_arg_immutable_error_code = """
def f(a: int) -> int {
    a = a + 1;
    return a;
}
"""


decl_builtin_immutable_error_code = """
print = 5;
"""


def test_decl_builtin_immutable_error():
    assert_transform_error(
        decl_builtin_immutable_error_code, ScopeError, "assign to immutable"
    )


def test_decl_arg_immutable_error():
    assert_transform_error(
        decl_arg_immutable_error_code, ScopeError, "assign to immutable"
    )


decl_def_immutable_error_code = """
def g() -> int {
    return 0;
}
g = 1;
"""


def test_decl_def_immutable_error():
    assert_transform_error(
        decl_def_immutable_error_code, ScopeError, "assign to immutable"
    )


decl_class_immutable_error_code = """
class C {
    let x: int;
}
C = 5;
"""


def test_decl_class_immutable_error():
    assert_transform_error(
        decl_class_immutable_error_code, ScopeError, "assign to immutable"
    )
