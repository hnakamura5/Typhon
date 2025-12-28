from ..assertion_utils import assert_transform, assert_transform_first_error
from ....src.Typhon.Grammar.syntax_errors import ScopeError

access_builtin_code = """
print(__file__)
"""
access_builtin_result = """
print(__file__)
"""


def test_access_builtin():
    assert_transform(access_builtin_code, access_builtin_result)


access_builtin_error_code = """
__file__ = "new_value";
print(__file__);
"""


def test_access_builtin_error():
    assert_transform_first_error(
        access_builtin_error_code, ScopeError, "assign to immutable"
    )
