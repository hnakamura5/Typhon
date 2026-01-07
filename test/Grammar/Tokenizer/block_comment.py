from ..assertion_utils import (
    show_token,
    assert_parse,
    RawTokenStreamAsserter,
    AllTokenAsserter,
)
from tokenize import (
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

block_comment_code = """
let x = 10 #(comment in line)#
"""
block_comment_result = """
x = 10
"""


def test_block_comment():
    show_token(block_comment_code)
    ta = RawTokenStreamAsserter(block_comment_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "x")
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (2, 8), (2, 10))
    ta.next(COMMENT, "#(comment in line)#", (2, 11), (2, 30))
    ta.next(NEWLINE, "\n", (2, 30), (2, 31))  # The position after the comment
    ta.next(ENDMARKER, "")
    assert_parse(block_comment_code, block_comment_result)


block_comment_multiline_code = """
let x = 10 #(
multi
line
comment)# + 20
"""
block_comment_multiline_result = """
x = 10 + 20
"""


def test_block_comment_multiline():
    show_token(block_comment_multiline_code)
    ta = RawTokenStreamAsserter(block_comment_multiline_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "x")
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (2, 8), (2, 10))
    ta.next(COMMENT, "#(\nmulti\nline\ncomment)#", (2, 11), (5, 9))
    ta.next(OP, "+", (5, 10), (5, 11))
    ta.next(NUMBER, "20", (5, 12), (5, 14))
    ta.next(NEWLINE, "\n", (5, 14), (5, 15))
    ta.next(ENDMARKER, "")
    assert_parse(block_comment_multiline_code, block_comment_multiline_result)


block_comment_consecutive_code = """
let x = 10 #(first comment)# #(
second comment)# + 20
"""
block_comment_consecutive_result = """
x = 10 + 20
"""


def test_block_comment_consecutive():
    show_token(block_comment_consecutive_code)
    ta = RawTokenStreamAsserter(block_comment_consecutive_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "x")
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (2, 8), (2, 10))
    ta.next(COMMENT, "#(first comment)#", (2, 11), (2, 28))
    ta.next(COMMENT, "#(\nsecond comment)#", (2, 29), (3, 16))
    ta.next(OP, "+", (3, 17), (3, 18))
    ta.next(NUMBER, "20", (3, 19), (3, 21))
    ta.next(NEWLINE, "\n", (3, 21), (3, 22))
    ta.next(ENDMARKER, "")
    assert_parse(block_comment_consecutive_code, block_comment_consecutive_result)


block_comment_sandwich_code = """
#(first comment)#
let x #(second comment)# = 10 #(third
comment)# + 20  #(last
comment
)#
    - 30
"""
block_comment_sandwich_result = """
x = 10 + 20 - 30
"""


def test_block_comment_sandwich():
    show_token(
        block_comment_sandwich_code, show_python_token=False, show_typhon_token=False
    )
    ta = RawTokenStreamAsserter(block_comment_sandwich_code)
    ta.next(NEWLINE, "\n")
    ta.next(COMMENT, "#(first comment)#", (2, 0), (2, 17))
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let", (3, 0), (3, 3))
    ta.next(NAME, "x")
    ta.next(COMMENT, "#(second comment)#", (3, 6), (3, 24))
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (3, 27), (3, 29))
    ta.next(COMMENT, "#(third\ncomment)#", (3, 30), (4, 9))
    ta.next(OP, "+", (4, 10), (4, 11))
    ta.next(NUMBER, "20", (4, 12), (4, 14))
    ta.next(COMMENT, "#(last\ncomment\n)#", (4, 16), (6, 2))
    ta.next(NEWLINE, "\n", (6, 2), (6, 3))
    ta.next(INDENT)
    ta.next(OP, "-", (7, 4), (7, 5))
    ta.next(NUMBER, "30", (7, 6), (7, 8))
    ta.next(NEWLINE, "\n", (7, 8), (7, 9))
    ta.next(DEDENT)
    ta.next(ENDMARKER, "")
    assert_parse(block_comment_sandwich_code, block_comment_sandwich_result)


block_comment_string_code = """
let s = "This is #(not a comment)# string" #(this is a comment)#
"""
block_comment_string_result = """
s = 'This is #(not a comment)# string'
"""


def test_block_comment_string():
    ta = RawTokenStreamAsserter(block_comment_string_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "s")
    ta.next(OP, "=")
    ta.next(STRING, '"This is #(not a comment)# string"', (2, 8), (2, 42))
    ta.next(COMMENT, "#(this is a comment)#", (2, 43), (2, 64))
    ta.next(NEWLINE, "\n", (2, 64), (2, 65))
    ta.next(ENDMARKER, "")
    assert_parse(block_comment_string_code, block_comment_string_result)


block_comment_f_string_code = """
def func(i: int) {
    let s = f'This is #(not a comment)# {i#(but this is a comment)#} inside f-string' #(and this is a comment)#
    print(s)
}
"""
block_comment_f_string_result = """
def func(i: int):
    s = f'This is #(not a comment)# {i} inside f-string'
    print(s)
"""


def test_block_comment_f_string():
    show_token(block_comment_f_string_code)
    ta = RawTokenStreamAsserter(block_comment_f_string_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "def")
    ta.next(NAME, "func")
    ta.next(OP, "(")
    ta.next(NAME, "i")
    ta.next(OP, ":")
    ta.next(NAME, "int")
    ta.next(OP, ")")
    ta.next(OP, "{")
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "s")
    ta.next(OP, "=")
    ta.next(FSTRING_START, "f'", (3, 12), (3, 14))
    ta.next(FSTRING_MIDDLE, "This is #(not a comment)# ", (3, 14), (3, 40))
    ta.next(OP, "{", (3, 40), (3, 41))
    ta.next(NAME, "i", (3, 41), (3, 42))
    ta.next(COMMENT, "#(but this is a comment)#", (3, 42), (3, 67))
    ta.next(OP, "}", (3, 67), (3, 68))
    ta.next(FSTRING_MIDDLE, " inside f-string", (3, 68), (3, 84))
    ta.next(FSTRING_END, "'", (3, 84), (3, 85))
    ta.next(COMMENT, "#(and this is a comment)#", (3, 86), (3, 111))
    ta.next(NEWLINE, "\n", (3, 111), (3, 112))
    ta.next(NAME, "print")
    ta.next(OP, "(")
    ta.next(NAME, "s")
    ta.next(OP, ")")
    ta.next(NEWLINE, "\n", (4, 12), (4, 13))
    ta.next(OP, "}")
    ta.next(NEWLINE, "\n", (5, 1), (5, 2))
    ta.next(ENDMARKER, "")

    assert_parse(
        block_comment_f_string_code,
        block_comment_f_string_result,
        # Python tokenizer fails to parse block comments because
        # it becomes line comment that terminates f-string invalidly
        show_python_token=False,
    )


block_comment_docstring_code = '''
def func() {
    """
    This is a docstring with #(not a comment inside.
    This should not be treated as a comment.
    """
    pass
}
'''
block_comment_docstring_result = '''
def func():
    """
    This is a docstring with #(not a comment inside.
    This should not be treated as a comment.
    """
    pass
'''


def test_block_comment_docstring():
    assert_parse(block_comment_docstring_code, block_comment_docstring_result)


block_comment_docstring_single_code = """
def func() {
    'This is a single-quoted docstring with #(not a comment)# inside.'
    pass
}
"""
block_comment_docstring_single_result = '''
def func():
    """This is a single-quoted docstring with #(not a comment)# inside."""
    pass
'''


def test_block_comment_docstring_single():
    assert_parse(
        block_comment_docstring_single_code, block_comment_docstring_single_result
    )


block_comment_docstring_f_string_code = '''
def func() {
    f"""
    This is a f-string docstring with #(not a comment)#
    inside. {42#(comment inside interpolation)#}"""
    pass
}
'''
block_comment_docstring_f_string_result = """
def func():
    f'\\n    This is a f-string docstring with #(not a comment)#\\n    inside. {42}'
    pass
"""


def test_block_comment_docstring_f_string():
    assert_parse(
        block_comment_docstring_f_string_code,
        block_comment_docstring_f_string_result,
        show_python_token=False,
    )


string_inside_block_comment_code = """
let x = 10 #("This is a string inside block comment)# + " "
"""
string_inside_block_comment_result = """
x = 10 + ' '
"""


def test_string_inside_block_comment():
    show_token(string_inside_block_comment_code)
    ta = RawTokenStreamAsserter(string_inside_block_comment_code)
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "x")
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (2, 8), (2, 10))
    ta.next(COMMENT, '#("This is a string inside block comment)#', (2, 11), (2, 53))
    ta.next(OP, "+", (2, 54), (2, 55))
    ta.next(STRING, '" "', (2, 56), (2, 59))
    ta.next(NEWLINE, "\n", (2, 59), (2, 60))
    ta.next(ENDMARKER, "")
    assert_parse(
        string_inside_block_comment_code,
        string_inside_block_comment_result,
        show_python_token=False,
    )
    aa = AllTokenAsserter(string_inside_block_comment_code)
    aa.assert_length(9)
    aa.next(NAME, "let")
    aa.next(NAME, "x")
    aa.next(OP, "=")
    aa.next(NUMBER, "10", (2, 8), (2, 10))
    aa.next(COMMENT, '#("This is a string inside block comment)#', (2, 11), (2, 53))
    aa.next(OP, "+", (2, 54), (2, 55))
    aa.next(STRING, '" "', (2, 56), (2, 59))
    aa.next(NEWLINE, "\n", (2, 59), (2, 60))
    aa.next(ENDMARKER, "")
