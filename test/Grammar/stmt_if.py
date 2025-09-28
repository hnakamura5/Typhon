from ..assertion_utils import assert_ast_equals

empty_if_code = """
if (True) {
}
"""
empty_if_result = """
if True:
    pass
"""


def test_stmt_if_empty():
    assert_ast_equals(empty_if_code, empty_if_result)


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
    assert_ast_equals(if_else_code, if_else_result)


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
    assert_ast_equals(if_nested_code, if_nested_result)
