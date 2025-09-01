from ..assertion_utils import assert_ast_equals, assert_ast_type
from ...src.Grammar.typhon_ast import is_var, is_let
import ast

code_for = """
for (let i in range(10)) {
    print(i);
}
"""
result_for = """
for i in range(10):
    print(i)
"""


def test_stmt_for():
    parsed = assert_ast_equals(code_for, result_for)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_let(for_stmt)


code_async_for = """
async for (let i in async_range(10)) {
    await f(i);
}
"""
result_async_for = """
async for i in async_range(10):
    await f(i)
"""


def test_stmt_async_for():
    parsed = assert_ast_equals(code_async_for, result_async_for)
    async_for_stmt = assert_ast_type(parsed.body[0], ast.AsyncFor)
    assert is_let(async_for_stmt)


code_for_typed = """
for (var i: int in range(10)) {
    print(i);
}
"""
# TODO: Type annotation as type_comment
result_for_typed = """
for i in range(10):
    print(i)
"""


def test_stmt_for_typed():
    parsed = assert_ast_equals(code_for_typed, result_for_typed)
    for_stmt = assert_ast_type(parsed.body[0], ast.For)
    assert is_var(for_stmt)
