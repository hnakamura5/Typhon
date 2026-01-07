from ..assertion_utils import (
    show_token,
    assert_parse,
    assert_raw_tokenize_error,
    RawTokenStreamAsserter,
    AllTokenAsserter,
)
from tokenize import (
    TokenError,
    NAME,
    OP,
    NEWLINE,
    ENDMARKER,
    NUMBER,
    COMMENT,
    INDENT,
    DEDENT,
    STRING,
    FSTRING_START,
    FSTRING_MIDDLE,
    FSTRING_END,
)
from src.Typhon.Driver.debugging import set_debug_verbose

# This file test the cases that becomes syntax error (TokenError) in Python's original tokenizer

newline_error_code = """
if (True) {
    print(True)
}
if (False {
    print(False)
"""


def test_newline_error():
    assert_raw_tokenize_error(newline_error_code, TokenError)
    ta = RawTokenStreamAsserter(newline_error_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "True")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "True")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "False")
    ta.next(OP, "{")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "False")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")


indent_error_code = """
if (True) {
    print(True)
}
    if (False) {
        print(False)
"""


def test_indent_error():
    assert_raw_tokenize_error(indent_error_code, TokenError)
    ta = RawTokenStreamAsserter(indent_error_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "True")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "True")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n")
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n")
    ta.next(INDENT)
    ta.next(NAME, "if")
    ta.next(OP, "(")
    ta.next(NAME, "False")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "False")
    ta.next(OP, ")")
    ta.next(DEDENT)
    ta.next(NEWLINE, "\n")
    ta.next(ENDMARKER, "")
