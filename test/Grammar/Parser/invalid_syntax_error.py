from ..assertion_utils import (
    assert_parse_first_error,
    with_parser_verbose,
    assert_parse_error_recovery,
    Range,
    Pos,
)


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


# Skip the broken part and recover the second declaration
panic_simple_code = """
let x = 1
!! garbage tokens !!
let y = 2
"""
panic_simple_recovery = """
x = 1
pass
y = 2
"""


def test_panic_simple_recovery():
    assert_parse_error_recovery(
        panic_simple_code,
        panic_simple_recovery,
        [("unknown token", Range(Pos(2, 0), Pos(2, 21)))],
    )


# Recover the class definition
panic_definition_code = """
def [] broken_func(a, #) -> {
    return 1
}
class RecoveredClass {}
"""
panic_definition_recovery = """
def _typh_invalid_name():
    []
    broken_func
    pass
    return 1

class RecoveredClass:
    pass
"""


def test_panic_definition_recovery():
    with with_parser_verbose():
        assert_parse_error_recovery(
            panic_definition_code,
            panic_definition_recovery,
            [
                ("expected '('", Range(Pos(1, 3), Pos(1, 4))),
                ("expected ')'", Range(Pos(1, 3), Pos(1, 4))),
                ("expected function name", Range(Pos(1, 3), Pos(1, 4))),
                ("expected '{'", Range(Pos(1, 4), Pos(1, 5))),
                ("unknown tokens", Range(Pos(1, 18), Pos(1, 21))),
            ],
        )


# Recover the second declaration
panic_inside_block_code = """
if (true) {
    let a = 1
    1 + * / 2
    let b = 2
}
"""
panic_inside_block_recovery = """
if true:
    a = 1
    1
    pass
    b = 2
"""


def test_panic_inside_block_recovery():
    assert_parse_error_recovery(
        panic_inside_block_code,
        panic_inside_block_recovery,
        [
            ("unknown tokens", Range(Pos(3, 6), Pos(3, 14))),
        ],
    )
