from ..assertion_utils import assert_parse, assert_parse_error_recovery, Range, Pos

empty_if_code = """
if (True) {
}
"""
empty_if_result = """
if True:
    pass
"""


def test_stmt_if_empty():
    assert_parse(empty_if_code, empty_if_result)


if_else_code = """
if (True) {
} elif (False) {
  return 0;
} else {
}
"""
if_else_result = """
if True:
    pass
elif False:
    return 0
else:
    pass
"""


def test_stmt_if_else():
    assert_parse(if_else_code, if_else_result)


if_nested_code = """
if (True) {
    if (False) {
        return 1;
        } elif (True) {
            return 2;
                }
    return 3;
} else {
    return 4;
}
"""
if_nested_result = """
if True:
    if False:
        return 1
    elif True:
        return 2
    return 3
else:
    return 4
"""


def test_stmt_if_nested():
    assert_parse(if_nested_code, if_nested_result)


if_parenless_code = """
if True {
}
if (False {
}
"""
if_parenless_recover = """
if True:
    pass
if False:
    pass
"""


def test_if_parenless_recovery():
    assert_parse_error_recovery(
        if_parenless_code,
        if_parenless_recover,
        [
            ("expected '('", Range(Pos(1, 2), Pos(1, 3))),
            ("expected ')'", Range(Pos(1, 7), Pos(1, 8))),
            ("expected ')'", Range(Pos(3, 9), Pos(3, 10))),
        ],
    )


if_braceless_code = """
if (True)
    print(True)
}
if (False) {
    print(False)
"""
if_braceless_recover = """
if True:
    print(True)
if False:
    print(False)
"""


def test_if_braceless_recovery():
    assert_parse_error_recovery(
        if_braceless_code,
        if_braceless_recover,
        [  # TODO: This is not wrong but not so good position
            ("expected '{'", Range(Pos(2, 4), Pos(2, 5))),
            ("expected '}'", Range(Pos(5, 16), Pos(5, 17))),
        ],
    )
