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


paren_recovery_code = """
let x = (1 + * 2) * (3 * a// 4 5)
if (x > 10) {
    print(x)
}
"""
paren_recovery_recovery = """
x = ... * ...
if x > 10:
    print(x)
"""


def test_paren_recovery():
    assert_parse_error_recovery(
        paren_recovery_code,
        paren_recovery_recovery,
        [
            ("unknown tokens", Range(Pos(1, 8), Pos(1, 17))),
            ("unknown tokens", Range(Pos(1, 20), Pos(1, 33))),
        ],
    )


bracket_recovery_code = """
let x = [1, 2, * 3, 4  5 6 +]
"""
bracket_recovery_recovery = """
x = ...
"""


def test_bracket_recovery():
    assert_parse_error_recovery(
        bracket_recovery_code,
        bracket_recovery_recovery,
        [
            ("unknown tokens", Range(Pos(1, 8), Pos(1, 29))),
        ],
    )


brace_recovery_code = """
let x = {a: 1, b: 2, c: * 3, d: 4 5 6}
"""
brace_recovery_recovery = """
x = ...
"""


def test_brace_recovery():
    assert_parse_error_recovery(
        brace_recovery_code,
        brace_recovery_recovery,
        [
            ("unknown tokens", Range(Pos(1, 8), Pos(1, 38))),
        ],
    )


record_recovery_code = """
let x = {|a: 1, b: 2, c: * 3, d: 4 5 6|}
"""
record_recovery_recovery = """x = ...
"""


def test_record_recovery():
    assert_parse_error_recovery(
        record_recovery_code,
        record_recovery_recovery,
        [
            ("unknown tokens", Range(Pos(1, 8), Pos(1, 40))),
        ],
    )


for_if_clause_paren_recovery_code = """
let xs = [for var i in range(5) if i > 0 yield i]
"""
for_if_clause_paren_recovery_result = """
xs = [i for i in range(5) if i > 0]
"""


def test_for_if_clause_paren_recovery():
    assert_parse_error_recovery(
        for_if_clause_paren_recovery_code,
        for_if_clause_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 13), Pos(1, 14))),
            ("expected ')'", Range(Pos(1, 31), Pos(1, 32))),
            ("expected '('", Range(Pos(1, 34), Pos(1, 35))),
            ("expected ')'", Range(Pos(1, 40), Pos(1, 41))),
        ],
    )


if_comp_internal_paren_recovery_code = """
let x = (if True 1 else 0)
"""
if_comp_internal_paren_recovery_result = """
x = 1 if True else 0
"""


def test_if_comp_internal_paren_recovery():
    assert_parse_error_recovery(
        if_comp_internal_paren_recovery_code,
        if_comp_internal_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 11), Pos(1, 12))),
            ("expected ')'", Range(Pos(1, 16), Pos(1, 17))),
        ],
    )


if_comp_elif_paren_recovery_code = """
let x = (if (True) 1 elif False 2 else 0)
"""
if_comp_elif_paren_recovery_result = """
x = 1 if True else 2 if False else 0
"""


def test_if_comp_elif_paren_recovery():
    assert_parse_error_recovery(
        if_comp_elif_paren_recovery_code,
        if_comp_elif_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 25), Pos(1, 26))),
            ("expected ')'", Range(Pos(1, 31), Pos(1, 32))),
        ],
    )


with_comp_internal_paren_recovery_code = """
let value = (with let f = open("x.txt")) f.read())
"""
with_comp_internal_paren_recovery_result = """
value = __with_control
"""


def test_with_comp_internal_paren_recovery():
    assert_parse_error_recovery(
        with_comp_internal_paren_recovery_code,
        with_comp_internal_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 17), Pos(1, 18))),
        ],
    )


try_comp_except_paren_recovery_code = """
let x = (try 1 / 0 except * ZeroDivisionError as e 0)
"""
try_comp_except_paren_recovery_result = """
x = __try_comp
"""


def test_try_comp_except_paren_recovery():
    assert_parse_error_recovery(
        try_comp_except_paren_recovery_code,
        try_comp_except_paren_recovery_result,
        [],
    )


match_comp_internal_paren_recovery_code = """
let x = (match y case (1) 1)
"""
match_comp_internal_paren_recovery_result = """
x = __match_comp
"""


def test_match_comp_internal_paren_recovery():
    assert_parse_error_recovery(
        match_comp_internal_paren_recovery_code,
        match_comp_internal_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 14), Pos(1, 15))),
            ("expected ')'", Range(Pos(1, 16), Pos(1, 17))),
        ],
    )


match_comp_case_paren_recovery_code = """
let x = (match (y) case 1 1)
"""
match_comp_case_paren_recovery_result = """
x = __match_comp
"""


def test_match_comp_case_paren_recovery():
    assert_parse_error_recovery(
        match_comp_case_paren_recovery_code,
        match_comp_case_paren_recovery_result,
        [],
    )


while_comp_internal_paren_recovery_code = """
let x = (while True yield 1)
"""
while_comp_internal_paren_recovery_result = """
x = __while_comp
"""


def test_while_comp_internal_paren_recovery():
    assert_parse_error_recovery(
        while_comp_internal_paren_recovery_code,
        while_comp_internal_paren_recovery_result,
        [
            ("expected '('", Range(Pos(1, 14), Pos(1, 15))),
            ("expected ')'", Range(Pos(1, 19), Pos(1, 20))),
        ],
    )
