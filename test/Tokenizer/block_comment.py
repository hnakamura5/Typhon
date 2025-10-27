from ..assertion_utils import show_token, assert_ast_equals, RawTokenStreamAsserter
from tokenize import NAME, OP, NEWLINE, ENDMARKER, NUMBER, COMMENT, INDENT, DEDENT
from ...src.Typhon.Driver.debugging import set_debug_mode

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
    assert_ast_equals(block_comment_code, block_comment_result)


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
    assert_ast_equals(block_comment_multiline_code, block_comment_multiline_result)


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
    assert_ast_equals(block_comment_consecutive_code, block_comment_consecutive_result)


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
    set_debug_mode(True)
    show_token(block_comment_sandwich_code)
    ta = RawTokenStreamAsserter(block_comment_sandwich_code)
    ta.next(NEWLINE, "\n")
    ta.next(COMMENT, "#(first comment)#", (2, 0), (2, 17))
    ta.next(NEWLINE, "\n")
    ta.next(NAME, "let")
    ta.next(NAME, "x")
    ta.next(COMMENT, "#(second comment)#", (3, 6), (3, 24))
    ta.next(OP, "=")
    ta.next(NUMBER, "10", (3, 27), (3, 29))
    ta.next(COMMENT, "#(third\ncomment)#", (3, 30), (4, 9))
    ta.next(OP, "+", (4, 10), (4, 11))
    ta.next(NUMBER, "20", (4, 12), (4, 14))
    ta.next(COMMENT, "#(last\ncomment\n)#", (4, 16), (6, 2))
    ta.next(NEWLINE, "\n", (6, 2), (6, 3))
    ta.next(INDENT, "    ", (7, 0), (7, 4))
    ta.next(OP, "-", (7, 4), (7, 5))
    ta.next(NUMBER, "30", (7, 6), (7, 8))
    ta.next(NEWLINE, "\n", (7, 8), (7, 9))
    ta.next(DEDENT, "", (8, 0), (8, 0))
    ta.next(ENDMARKER, "")
    assert_ast_equals(block_comment_sandwich_code, block_comment_sandwich_result)
