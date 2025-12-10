from ..assertion_utils import assert_ast_error

invalid_if_paren_code = """
if True {print("Hello");}
"""
invalid_if_brace_code = """
if (True) print("Hello");
"""


def test_invalid_if():
    assert_ast_error(invalid_if_paren_code, SyntaxError, "expected '('")
    assert_ast_error(invalid_if_brace_code, SyntaxError, "expected '{'")


invalid_if_let_code = """
if (let x = 10) print(x);
"""


def test_invalid_if_let():
    assert_ast_error(invalid_if_let_code, SyntaxError, "expected '{'")


invalid_elif_code = """
if (True) {
    print("Hello");
} elif (False) print("World");
}
"""


def test_invalid_elif():
    assert_ast_error(invalid_elif_code, SyntaxError, "expected '{'")


invalid_while_paren_code = """
while True {print("Hello")}
"""
invalid_while_brace_code = """
while (True) print("Hello")
"""


def test_invalid_while():
    assert_ast_error(invalid_while_paren_code, SyntaxError, "expected '('")
    assert_ast_error(invalid_while_brace_code, SyntaxError, "expected '{'")


invalid_while_let_code = """
while (let x = 10) print(x)
"""


def test_invalid_while_let():
    assert_ast_error(invalid_while_let_code, SyntaxError, "expected '{'")


invalid_for_paren_code = """
for let i in range(10) {
    print(i);
}
"""


def test_invalid_for_paren():
    assert_ast_error(invalid_for_paren_code, SyntaxError, "expected '('")


invalid_with_brace_code = """
with (let x = open('file.txt')) print(x); }
"""


def test_invalid_with_brace():
    assert_ast_error(invalid_with_brace_code, SyntaxError, "expected '{'")


invalid_try_brace_code = """
try print("Hello");
"""


def test_invalid_try_brace():
    assert_ast_error(invalid_try_brace_code, SyntaxError, "expected '{'")


invalid_except_paren_code = """
try {} except ValueError print("Error");
"""
invalid_except_brace_code = """
try {
    print("Hello");
} except (ValueError) print("Error");
"""
invalid_except_star_none_code = """
try {
    print("Hello");
} except * {print("Error")}
"""


def test_invalid_except():
    assert_ast_error(invalid_except_paren_code, SyntaxError, "expected '('")
    assert_ast_error(invalid_except_brace_code, SyntaxError, "expected '{'")
    assert_ast_error(invalid_except_star_none_code, SyntaxError, "expected one or more")


invalid_finally_brace_code = """
try {
    print("Hello");
} finally print("Done");
"""


def test_invalid_finally_brace():
    assert_ast_error(invalid_finally_brace_code, SyntaxError, "expected '{'")


invalid_match_paren_code = """
match x { case(1) {print("No cases")} }
"""
invalid_match_brace_code = """
match (x) case (1) {print("No cases")}
"""


def test_invalid_match_paren():
    assert_ast_error(invalid_match_paren_code, SyntaxError, "expected '('")
    assert_ast_error(invalid_match_brace_code, SyntaxError, "expected '{'")


invalid_case_paren_code = """
match (x) {
    case 1 print("No braces")
}
"""
invalid_case_brace_code = """
match (x) {
    case (1) print("No braces")
}
"""


def test_invalid_case_paren():
    assert_ast_error(invalid_case_paren_code, SyntaxError, "expected '('")
    assert_ast_error(invalid_case_brace_code, SyntaxError, "expected '{'")


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
    assert_ast_error(invalid_as_pattern_code, SyntaxError, "invalid as pattern target")
    assert_ast_error(
        invalid_as_pattern_underscore_code,
        SyntaxError,
        "cannot use '_' as a target",
    )
    assert_ast_error(
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
    assert_ast_error(invalid_function_def_code, SyntaxError, "expected '{'")
    assert_ast_error(invalid_function_def_untype_code, SyntaxError, "expected '{'")
    assert_ast_error(invalid_function_def_no_type_code, SyntaxError, "use '->'")


invalid_class_code = """
class MyClass
    def __init__(self) {
        pass;
    }
"""
invalid_class_sub_code = """
class MyClass(ParentClass)
    def __init__(self) {
        pass;
    }
"""


def test_invalid_class_def():
    assert_ast_error(invalid_class_code, SyntaxError, "expected '{'")
    assert_ast_error(invalid_class_sub_code, SyntaxError, "expected '{'")
