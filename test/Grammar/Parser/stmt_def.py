from ..assertion_utils import (
    assert_parse,
    show_token,
    assert_token,
    assert_parse_error_recovery,
    Range,
    Pos,
    with_parser_verbose,
)

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
    assert_parse(code_def, result_def)


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
    assert_parse(code_def_typed, result_def_typed)


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
    assert_parse(code_def_async_typed, result_def_async_typed)


code_def_parenless = """
def func (x: int {
    return None;
}
"""
recover_def_parenless = """
def func(x: int):
    return None
"""


def test_stmt_def_parenless_recovery():
    assert_parse_error_recovery(
        code_def_parenless,
        recover_def_parenless,
        [
            ("expected ')'", Range(Pos(1, 16), Pos(1, 17))),
        ],
    )


code_def_braceless = """
def func (x: int) {
    return None
"""
recover_def_braceless = """
def func(x: int):
    return None
"""


def test_stmt_def_braceless_recovery():
    assert_parse_error_recovery(
        code_def_braceless,
        recover_def_braceless,
        [
            ("expected '}'", Range(Pos(2, 15), Pos(2, 16))),
        ],
    )


code_def_nameless = """
def(x: int) {
    return None;
}
"""
recover_def_nameless = """
def _typh_invalid_name(x: int):
    return None
"""


def test_stmt_def_nameless_recovery():
    assert_parse_error_recovery(
        code_def_nameless,
        recover_def_nameless,
        [("expected function name", Range(Pos(1, 3), Pos(1, 4)))],
    )
