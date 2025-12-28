from ..assertion_utils import assert_parse, with_parser_verbose

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
