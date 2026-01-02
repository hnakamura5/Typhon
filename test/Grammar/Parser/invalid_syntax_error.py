from ..assertion_utils import assert_parse_first_error, with_parser_verbose

invalid_if_let_code = """
if (let x = 10) print(x);
"""


def test_invalid_if_let():
    assert_parse_first_error(invalid_if_let_code, SyntaxError, "expected '{'")


invalid_while_paren_code = """
while True {print("Hello")}
"""
invalid_while_brace_code = """
while (True) print("Hello")
"""


def test_invalid_while():
    assert_parse_first_error(invalid_while_paren_code, SyntaxError, "expected '('")
    assert_parse_first_error(invalid_while_brace_code, SyntaxError, "expected '{'")


invalid_while_let_code = """
while (let x = 10) print(x)
"""


def test_invalid_while_let():
    assert_parse_first_error(invalid_while_let_code, SyntaxError, "expected '{'")


invalid_as_pattern_code = """
match (x) {
    case (y as) {print(y)}
}
"""
invalid_as_pattern_underscore_code = """
match (x) {
    case (y as _) {print("underscore")}
}
"""
invalid_class_pattern_code = """
match (x) {
    case (MyClass(x=a, b)) {print(a, b)}
}
"""


def test_invalid_as_pattern():
    assert_parse_first_error(
        invalid_as_pattern_code, SyntaxError, "invalid as pattern target"
    )
    assert_parse_first_error(
        invalid_as_pattern_underscore_code,
        SyntaxError,
        "cannot use '_' as a target",
    )
    assert_parse_first_error(
        invalid_class_pattern_code,
        SyntaxError,
        "positional patterns follow keyword patterns",
    )


invalid_function_def_code = """
def func(a, b) -> int
    print(a + b)
"""
invalid_function_def_untype_code = """
def func(a, b)
    print(a + b)
"""
invalid_function_def_no_type_code = """
def func(a, b):
    print(a + b)
"""


def test_invalid_function_def():
    assert_parse_first_error(invalid_function_def_code, SyntaxError, "expected '{'")
    assert_parse_first_error(
        invalid_function_def_untype_code, SyntaxError, "expected '{'"
    )
    # TODO:
    # assert_parse_first_error(invalid_function_def_no_type_code, SyntaxError, "use '->'")
