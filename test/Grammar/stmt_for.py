from .assertion_utils import assert_ast_equals

code_for = """
for (i in range(10)) {
    print(i);
}
"""
result_for = """
for i in range(10):
    print(i)
"""


def test_stmt_for():
    assert_ast_equals(code_for, result_for)


code_async_for = """
async for (i in async_range(10)) {
    await f(i);
}
"""
result_async_for = """
async for i in async_range(10):
    await f(i)
"""


def test_stmt_async_for():
    assert_ast_equals(code_async_for, result_async_for)
