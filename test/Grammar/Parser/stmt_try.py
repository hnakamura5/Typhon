from ..assertion_utils import (
    assert_parse,
    with_parser_verbose,
    assert_parse_error_recovery,
    Range,
    Pos,
)

try_code = """
try {
    raise TypeError;
} except {
    raise
}
"""
try_result = """
try:
    raise TypeError
except:
    raise
"""


def test_stmt_try():
    assert_parse(try_code, try_result)


try_finally_code = """
try {
    raise TypeError;
} except {
    raise
} finally {
    cleanup();
}
"""
try_finally_result = """
try:
    raise TypeError
except:
    raise
finally:
    cleanup()
"""


def test_stmt_try_finally():
    assert_parse(try_finally_code, try_finally_result)


try_except_else_code = """
try {
    raise TypeError;
} except {
    raise
} else {
    cleanup();
}
"""
try_except_else_result = """
try:
    raise TypeError
except:
    raise
else:
    cleanup()
"""


def test_stmt_try_except_else():
    assert_parse(try_except_else_code, try_except_else_result)


try_except_error_code = """
try {
    raise TypeError;
} except(TypeError as e) {
    raise
}
"""
try_except_error_result = """
try:
    raise TypeError
except TypeError as e:
    raise
"""


def test_stmt_try_except_error():
    assert_parse(try_except_error_code, try_except_error_result)


try_except_star_code = """
try {
    raise TypeError;
} except*(TypeError as e) {
    raise
}
"""
try_except_star_result = """
try:
    raise TypeError
except* TypeError as e:
    raise
"""


def test_stmt_try_except_star():
    assert_parse(try_except_star_code, try_except_star_result)


try_braceless_code = """
try print("Hello") except (e) { print("Error") }
"""
try_braceless_recovery = """
try:
    print('Hello')
except e:
    print('Error')
"""

_try_braceless_code = """
try print("Hello") except { print("Error") }
"""
_try_braceless_recovery = """
try:
    print('Hello')
except e:
    print('Error')
"""
# TODO: Is this recovery desirable?


def test_stmt_try_braceless_recovery():
    assert_parse_error_recovery(
        try_braceless_code,
        try_braceless_recovery,
        [
            ("expected '{'", Range(Pos(1, 4), Pos(1, 5))),
            ("expected '}'", Range(Pos(1, 18), Pos(1, 19))),
        ],
    )


except_parenless_code = """
try {} except ValueError print("Error");
"""
except_parenless_recover = """
try:
    pass
except ValueError:
    print('Error')
"""


def test_stmt_except_parenless_recovery():
    assert_parse_error_recovery(
        except_parenless_code,
        except_parenless_recover,
        [
            ("expected '('", Range(Pos(1, 13), Pos(1, 14))),
            ("expected ')'", Range(Pos(1, 24), Pos(1, 25))),
            ("expected '{'", Range(Pos(1, 25), Pos(1, 26))),
            ("expected '}'", Range(Pos(1, 39), Pos(1, 40))),
        ],
    )


except_braceless_code = """
try {
    print("Hello");
} except (ValueError) print("Error");
"""
except_braceless_recover = """
try:
    print('Hello')
except ValueError:
    print('Error')
"""


def test_stmt_except_braceless_recovery():
    assert_parse_error_recovery(
        except_braceless_code,
        except_braceless_recover,
        [
            ("expected '{'", Range(Pos(3, 22), Pos(3, 23))),
            ("expected '}'", Range(Pos(3, 36), Pos(3, 37))),
        ],
    )


except_star_none_code = """
try {
    print("Hello");
} except * {print("Error")}
"""
except_star_none_recover = """
try:
    print('Hello')
except*:
    print('Error')
"""


def test_stmt_except_star_none_recovery():
    assert_parse_error_recovery(
        except_star_none_code,
        except_star_none_recover,
        [
            ("expected one or more", Range(Pos(3, 2), Pos(3, 27))),
            ("expected '('", Range(Pos(3, 10), Pos(3, 11))),
            ("expected ')'", Range(Pos(3, 10), Pos(3, 11))),
            # TODO: Are they too many?
        ],
    )
