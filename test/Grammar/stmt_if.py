from ..assertion_utils import assert_ast_equals

code_empty_if = """
if (True) {
}
"""
result_empty_if = """
if True:
    pass
"""


def test_stmt_if_empty():
    assert_ast_equals(code_empty_if, result_empty_if)


code_if_else = """
if (True) {
} elif (False) {
  return 0;
} else {
}
"""
result_if_else = """
if True:
    pass
elif False:
    return 0
else:
    pass
"""


def test_stmt_if_else():
    assert_ast_equals(code_if_else, result_if_else)


code_if_nested = """
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
result_if_nested = """
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
    assert_ast_equals(code_if_nested, result_if_nested)
