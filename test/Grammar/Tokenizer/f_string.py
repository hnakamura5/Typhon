from ..assertion_utils import (
    show_token,
    assert_parse,
    TokenizerAsserter,
    assert_transform,
    set_parser_verbose,
    with_parser_verbose,
)
from src.Typhon.Grammar.typhon_ast import OPTIONAL_QUESTION, FORCE_UNWRAP
from src.Typhon.Driver.debugging import set_debug_verbose
from tokenize import (
    NAME,
    OP,
    NEWLINE,
    FSTRING_START,
    FSTRING_MIDDLE,
    FSTRING_END,
    ENDMARKER,
    NUMBER,
    STRING,
)


f_string_code = """
def func(value: int) {
    let s = f'Value: {value}'
    print(s)
}
func(42)
"""
f_string_result = """
def func(value: int):
    s = f'Value: {value}'
    print(s)
func(42)
"""


def test_f_string():
    assert_parse(f_string_code, f_string_result)


f_string_conversion_code = """
def func(value: int) {
    let s = f'Value: {value!r} end'
    print(s)
}
func(42)
"""
f_string_conversion_result = """
def func(value: int):
    s = f'Value: {value!r} end'
    print(s)
func(42)
"""


def test_f_string_conversion():
    ta = TokenizerAsserter(f_string_conversion_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "value")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "s")
    ta.next(OP, "=")
    ta.next(FSTRING_START, "f'")
    ta.next(FSTRING_MIDDLE, "Value: ")
    ta.next(OP, "{")
    ta.next(NAME, "value")
    ta.next(OP, "!")
    ta.next(NAME, "r")
    ta.next(OP, "}")
    ta.next(FSTRING_MIDDLE, " end")
    ta.next(FSTRING_END, "'")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "s")
    ta.next(OP, ")")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NUMBER, "42")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    assert_parse(f_string_conversion_code, f_string_conversion_result)


f_string_with_string_code = """
def func(value: int) {
    let s = f'Value: {'constant string'} and {value}'
    print(s)
}
func(42)
"""
f_string_with_string_result = """
def func(value: int):
    s = f"Value: {'constant string'} and {value}"
    print(s)
func(42)
"""


def test_f_string_with_string():
    show_token(f_string_with_string_code)
    set_debug_verbose(True)
    ta = TokenizerAsserter(f_string_with_string_code)
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "value")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NAME, "let")
    ta.next(NAME, "s")
    ta.next(OP, "=")
    ta.next(FSTRING_START, "f'")
    ta.next(FSTRING_MIDDLE, "Value: ")
    ta.next(OP, "{")
    ta.next(STRING, "'constant string'")
    ta.next(OP, "}")
    ta.next(FSTRING_MIDDLE, " and ")
    ta.next(OP, "{")
    ta.next(NAME, "value")
    ta.next(OP, "}")
    ta.next(FSTRING_END, "'")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "s")
    ta.next(OP, ")")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NUMBER, "42")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
    with with_parser_verbose(True):
        assert_parse(f_string_with_string_code, f_string_with_string_result)
