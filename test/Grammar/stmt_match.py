from .assertion_utils import assert_ast_equals

match_code = """
match (x) {
    case (1) {
        y = 1
    } case (2) {
        y = 2
    }
}
"""
match_result = """
match x:
    case 1:
        y = 1
    case 2:
        y = 2
"""


def test_stmt_match():
    assert_ast_equals(match_code, match_result)


match_with_guard_code = """
match (x) {
    case (1) if (y == 1) {
        z = 1
    }
    case (2) if (y == 2) {
        z = 2
    }
}
"""
match_with_guard_result = """
match x:
    case 1 if y == 1:
        z = 1
    case 2 if y == 2:
        z = 2
"""


def test_stmt_match_with_guard():
    assert_ast_equals(match_with_guard_code, match_with_guard_result)


match_sequence_code = """
match (x, y) {
    case (1, 2) {
        z = 1
    } case (2, 3) {
        z = 2
    }
}
"""
match_sequence_result = """
match (x, y):
    case [1, 2]:
        z = 1
    case [2, 3]:
        z = 2
"""
# Sequence is pattern printed using '[' and ']' by unparse.
# No semantic difference between '()' and '[]' in this pattern.


def test_stmt_match_sequence():
    assert_ast_equals(match_sequence_code, match_sequence_result)
