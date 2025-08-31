from ..assertion_utils import assert_ast_transform, assert_transform_error
from ...src.Grammar.syntax_errors import ScopeError

decl_let_code = """
let x = 10;
x = x + 5;
print(x);
"""
decl_let_result = """
x = 10
x = x + 5
print(x)
"""


def test_decl_let():
    assert_ast_transform(decl_let_code, decl_let_result)


decl_immutable_error_code = """
const y = 20;
y = y + 5;
"""


def test_decl_immutable_error():
    assert_transform_error(decl_immutable_error_code, ScopeError, "assign to immutable")


decl_duplicate_error_code = """
let z = 30;
let z = 40;
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
