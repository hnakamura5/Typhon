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
y = 2
"""


# def test_panic_simple_recovery():
#     with with_parser_verbose():
#         assert_parse_error_recovery(
#             panic_simple_code,
#             panic_simple_recovery,
#             [("unexpected token", Range(Pos(2, 0), Pos(2, 20)))],
#         )


# # Recover the class definition
# panic_definition_code = """
# def broken_func(a, #) -> {
#     return 1
# }
# class RecoveredClass {}
# """
# panic_definition_recovery = """
# class RecoveredClass:
#     pass
# """


# def test_panic_definition_recovery():
#     assert_parse_error_recovery(
#         panic_definition_code,
#         panic_definition_recovery,
#         [("unexpected token", Range(Pos(3, 1), Pos(3, 20)))],
#     )


# # Recover the second declaration
# panic_inside_block_code = """
# if (true) {
#     let a = 1
#     1 + * / 2
#     let b = 2
# }
# """
# panic_inside_block_recovery = """
# if (true) {
#     let a = 1
#     let b = 2
# }
# """


# def test_panic_inside_block_recovery():
#     assert_parse_error_recovery(
#         panic_inside_block_code,
#         panic_inside_block_recovery,
#         [("unexpected token", Range(Pos(3, 1), Pos(3, 20)))],
#     )
