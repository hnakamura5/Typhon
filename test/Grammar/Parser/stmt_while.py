from ..assertion_utils import assert_parse, assert_parse_error_recovery, Range, Pos

code_while = """
while (i < 10) {
    i += 1;
}
"""
result_while = """
while i < 10:
    i += 1
"""


def test_stmt_while():
    assert_parse(code_while, result_while)


code_while_parenless = """
while i < 10 {
    i += 1
    }
"""
code_while_parenless_recover = """
while i < 10:
    i += 1
"""


def test_stmt_while_parenless():
    assert_parse_error_recovery(
        code_while_parenless,
        code_while_parenless_recover,
        [
            ("expected '('", Range(Pos(1, 5), Pos(1, 6))),
            ("expected ')'", Range(Pos(1, 12), Pos(1, 13))),
        ],
    )


code_while_braceless = """
while(i < 10)
    i += 1
"""
code_while_braceless_recover = """
while i < 10:
    i += 1
"""


def test_stmt_while_braceless():
    assert_parse_error_recovery(
        code_while_braceless,
        code_while_braceless_recover,
        [
            ("expected '{'", Range(Pos(2, 4), Pos(2, 5))),
            ("expected '}'", Range(Pos(2, 10), Pos(2, 11))),
        ],
    )
