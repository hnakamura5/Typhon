from ..assertion_utils import assert_ast_equals, show_token, assert_token

code_def = """
def func() {
    return;
}
"""
result_def = """
def func():
    return
"""


def test_stmt_def():
    assert_ast_equals(code_def, result_def)


code_def_typed = """
def func(x: int) -> None {
    return None;
}
"""
result_def_typed = """
def func(x: int) -> None:
    return None

"""


def test_stmt_def_typed():
    assert_ast_equals(code_def_typed, result_def_typed)


code_def_async_typed = """
async def func(x: int) -> None {
    return None;
}
"""
result_def_async_typed = """
async def func(x: int) -> None:
    return None

"""


def test_stmt_def_async_typed():
    assert_ast_equals(code_def_async_typed, result_def_async_typed)
